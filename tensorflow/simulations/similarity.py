import struct
import numpy as np
from common_utils import console, dataset

from common_utils.dataset import DEFAULT_HEADER
HEADER = DEFAULT_HEADER


def cos_dist(x, y):
    """
    Computes cosine similarity complement of two vectors in positive space.

    Args:
        x: a numpy vector.
        y: a numpy vector.
    Returns:
        :math:`1-\\frac{\\langle x,y\\rangle}{|x||y|}`
    """
    return 1 - np.dot(x, y) / np.sqrt(np.dot(x, x) * np.dot(y, y))  # - np.dot(x, y)  #


def l2_dist(x, y):
    """
    Computes Euclidean distance of two vectors.

    Args:
        x: a numpy vector.
        y: a numpy vector.
    Returns:
        :math:`\\sqrt{\\langle x-y,x-y\\rangle}`
    """
    dxy = x - y
    return np.sqrt(np.dot(dxy, dxy))


class Similarity:
    """
    A class used to simulate user in similarity search.
    """

    def __init__(self):
        self.vectors = []
        self.dimension = 0
        self.len = 0

    def read_vectors(self, filename):
        """
        Loads similarity deep-feature vectors from a file.

        Args:
            filename: vectors' filename.
        """
        pt = console.ProgressTracker()
        pt.info(">> Reading similarity vectors...")

        dt = np.dtype(np.float32).newbyteorder("<")

        with dataset.read_file(filename, HEADER) as f:
            self.dimension = struct.unpack("<I", f.read(4))[0]
            self.len = 0

            buffer = f.read(4)  # read image id
            while buffer != b'':
                buffer = f.read(self.dimension * 4)
                vec = np.frombuffer(buffer, dtype=dt)
                self.vectors.append(vec)
                self.len += 1
                if self.len % 10000 == 0:
                    pt.progress_info("\t> Vectors read: {}", [self.len])
                buffer = f.read(4)  # read image id

    def get_distance_vector(self, query_index):
        """
        Computes distance of all vectors to the argument vector.

        Args:
            query_index: index of a vector to compute distances to.
        Returns:
            Vector of distances to the argument vector.
        """
        rank = np.zeros(self.len)
        query_vector = self.vectors[query_index].astype(np.float32)

        for i in range(self.len):
            rank[i] = cos_dist(query_vector, self.vectors[i].astype(np.float32))
        return rank

    def get_rank(self, query_index, searched_index):
        """
        Computes distance and rank of a searched vector(s) to a query vector.

        Args:
            query_index: a vector index or list of indexes. If list passed, an average of the vectors is used.
            searched_index: a vector index or list of indexes.
        Returns:
            Triple.
            A rank (list of ranks) of the searched vector(s) determined by the query vector.
            A distance (list of distances) of the searched vector(s) to the query vector.
            A rank of all vectors determined by the query vector.
        """
        if not isinstance(searched_index, list):
            searched_index = [searched_index]

        if not isinstance(query_index, list):
            query_index = [query_index]

        rank_vec = self.get_distance_vector(query_index[0])
        for index in query_index[1:]:
            rank_vec += self.get_distance_vector(index)

        index_vec = np.argsort(rank_vec)
        ret_list = []
        ret_distances = []

        for index in searched_index:
            ret_distances.append(abs(rank_vec[index] - rank_vec[index_vec[0]]))

            array_of_indexes = np.where(index_vec == index)[0]
            if len(array_of_indexes) != 1:
                raise Exception("Image ID " + index + " not found in array_of_indexes")
            ret_list.append(array_of_indexes[0])

        if len(ret_list) == 1:
            return ret_list[0], ret_distances[0], index_vec
        return ret_list, ret_distances, index_vec

    def _get_best_rank(self, image_indexes, searched_index, visualization, similarity_settings, n_reranks=1):
        """
        Takes initial ordering of a database and, given similarity settings,
        simulates user by iterative search for searched image.

        Args:
            image_indexes: initial ordering of a database.
            searched_index: index of the searched image.
            visualization: `SimilarityVisualization` class or None if visualization is not used.
            similarity_settings: `SimilaritySettings` class with settings.
            n_reranks: current depth of recursion.
        Returns:
            List of tuples.
            A number of reranks and its corresponding rank of the searched image.
        """
        if max(similarity_settings.n_reranks) < n_reranks:
            return []

        distances = []
        for index in image_indexes[:similarity_settings.display_size]:
            dist = cos_dist(self.vectors[index].astype(np.float32), self.vectors[searched_index].astype(np.float32))
            distances.append(dist)

        query_candidates = [image_indexes[i] for i in np.argsort(distances)[:similarity_settings.n_closest]]
        rank, distance, vector = self.get_rank(query_candidates, searched_index)

        if visualization is not None:
            visualization.new_iteration(vector[0], text=[
                "S {:d}".format(rank), "d={:}".format(distance)
            ])

        if distance > 0:
            l = self._get_best_rank(vector, searched_index, visualization, similarity_settings, n_reranks + 1)

            for rerank in similarity_settings.n_reranks:
                if rerank == n_reranks:
                    l.append((n_reranks, rank))
        else:
            l = []
            for rerank in similarity_settings.n_reranks:
                if rerank >= n_reranks:
                    l.append((rerank, rank))
        return l

    def get_best_rank(self, image_indexes, searched_index, similarity_settings, visualization=None):
        """
        Takes initial ordering of a database and, given similarity settings,
        simulates user by iterative search for searched image.

        Args:
            image_indexes: initial ordering of a database.
            searched_index: index of the searched image.
            similarity_settings: `SimilaritySettings` class with settings.
            visualization: `SimilarityVisualization` class or None if visualization is not used.
        Returns:
            Dictionary of ranks for each similarity setting.
        """
        ranks = {}

        for disp_size in similarity_settings.display_size:
            for n_closest in similarity_settings.n_closest:
                results = self._get_best_rank(image_indexes, searched_index, visualization,
                                              SimilaritySettings(disp_size, n_closest, similarity_settings.n_reranks))

                for n_reranks, image_rank in results:
                    text = SimilaritySettings.gen_text_string_from_similarity(disp_size, n_closest, n_reranks)
                    ranks[text] = image_rank
        return ranks


class SimilaritySettings:
    """
    A class used holding similarity search settings.
    """

    def __init__(self, disp_size, n_closest, n_reranks):
        """
        Args:
            disp_size: number of top ranking images to consider for similarity reranking.
            n_closest: number of the most similar images to use as query.
            n_reranks: how many reranks to do for each image.
        """
        self.display_size = disp_size
        self.n_closest = n_closest
        self.n_reranks = n_reranks

    @staticmethod
    def gen_text_string_from_similarity(disp_size, n_closest, n_reranks):
        """
        Returns:
            A text representation of a given setting.
        """
        return "{:d}:{:d} {:d}x".format(disp_size, n_closest, n_reranks)

    def get_empty_configurations(self):
        """
        Returns:
            An empty ranking object based on this configuration.
        """
        r = {}
        for disp_size in self.display_size:
            for n_closest in self.n_closest:
                for n_reranks in self.n_reranks:
                    r[self.gen_text_string_from_similarity(disp_size, n_closest, n_reranks)] = None
        return r
