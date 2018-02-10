import os
import struct
import numpy as np
import multiprocessing as mp
from common_utils import console


def cos_dist(x, y):
    """
    Computes cosine similarity complement of two vectors in positive space.

    Args:
        x: a numpy vector.
        y: a numpy vector.
    Returns:
        :math:`1-\\frac{\\langle x,y\\rangle}{|x||y|}`
    """
    return 1 - np.dot(x, y) / (np.sqrt(np.dot(x, x)) * np.sqrt(np.dot(y, y)))


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

    def read_vectors(self, filename, val_type=np.float32):
        """
        Loads vectors from a file.

        Args:
            filename: vectors' filename.
            val_type: vector format, default *np.float32*.
        """
        pt = console.ProgressTracker()
        pt.info(">> Reading similarity vectors...")

        dt = np.dtype(val_type).newbyteorder('<')

        with open(filename, 'rb') as f:
            pt.info("\t> Dataset ID: " + str(struct.unpack('<I', f.read(4))[0]))
            self.len = struct.unpack('<I', f.read(4))[0]

            self.dimension = struct.unpack('<I', f.read(4))[0]

            for i in range(self.len):
                vec = np.frombuffer(f.read(self.dimension), dtype=dt)
                self.vectors.append(vec)

    def get_distance_vector(self, query_index):
        """
        Computes distance of all vectors to the argument vector.

        Args:
            query_index: index of a vector to compute distances to.
        Returns:
            Vector of distances to the argument vector.
        """
        ranks = []

        def calc_distance(indexes):
            res = np.zeros(len(indexes))
            for i0, iv in enumerate(indexes):
                res[i0] = cos_dist(self.vectors[query_index], self.vectors[iv])
            return res, indexes

        def calc_callback(vector, indexes):
            ranks.append((indexes[0], vector))

        r = range(self.len)
        processes = os.cpu_count()
        ind = []

        for i in range(processes - 1):
            ind.append(r[self.len // processes * i: self.len // processes * (i + 1)])
        ind.append(r[self.len // processes * (processes - 1):])

        with mp.Pool(processes=processes) as pool:
            for i in range(processes):
                pool.apply_async(calc_distance, args=(ind[i],), callback=calc_callback)

            pool.close()
            pool.join()

        ranks.sort(key=lambda t: t[0])
        return np.concatenate([t[1] for t in ranks])

    def get_rank(self, query_index, searched_index):
        """
        Computes distance and rank of a searched vector(s) to a query vector.

        Args:
            query_index: a vector index or list of indexes. If list passed, an average is used.
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

    def _get_best_rank(self, image_indexes, searched_index, visualization, similarity_settings, n_reranks = 1):
        """
        Takes initial ordering of a database and, given similarity settings,
        simulates user by iterative search for searched image.

        Args:
            image_indexes: initial ordering of a database.
            visualization:
            searched_index: index of the searched image.
            similarity_settings:
            n_reranks: current depth of recursion.
        Returns:
            List of tuples.
            A number of reranks and a rank of the searched image.
        """
        if max(similarity_settings.n_reranks) < n_reranks:
            return []

        distances = []
        for index in image_indexes[:similarity_settings.display_size]:
            dist = cos_dist(self.vectors[index], self.vectors[searched_index])
            distances.append(dist)

        query_candidates = [image_indexes[i] for i in np.argsort(distances)[:similarity_settings.n_closest]]
        rank, distance, vector = self.get_rank(query_candidates, searched_index)

        if visualization is not None:
            visualization.new_iteration(vector[0], instance=similarity_settings, text=[
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
            similarity_settings:
            visualization:
        Returns:
            Dictionary of ranks for each similarity setting.
        """
        ranks = {}

        for disp_size in similarity_settings.display_size:
            for n_closest in similarity_settings.n_closest:
                results = self._get_best_rank(image_indexes, searched_index, visualization,
                                              SimilaritySettings(disp_size, n_closest, similarity_settings.n_reranks))

                for n_reranks, image_rank in results:
                    text = self.gen_text_string_from_similarity(disp_size, n_closest, n_reranks)
                    ranks[text] = image_rank
        return ranks

    @staticmethod
    def gen_text_string_from_similarity(disp_size, n_closest, n_reranks):
        return "{:d}:{:d} {:d}x".format(disp_size, n_closest, n_reranks)


class SimilaritySettings:
    def __init__(self, disp_size, n_closest, n_reranks):
        self.display_size = disp_size
        self.n_closest = n_closest
        self.n_reranks = n_reranks
