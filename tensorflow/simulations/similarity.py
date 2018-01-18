import os
import struct
import random
import numpy as np
from common_utils import console
from simulations import simulation_utils


class Similarity:
    VECTORS = []
    DIMENSION = 0

    def read_vectors(self, filename, astype=None):
        pt = console.ProgressTracker()
        pt.info(">> Reading similarity vectors...")

        dt = np.dtype(np.byte).newbyteorder('<')

        with open(filename, 'rb') as f:
            pt.info("\t> Dataset ID: " + str(struct.unpack('<I', f.read(4))[0]))
            count = struct.unpack('<I', f.read(4))[0]
            self.DIMENSION = struct.unpack('<I', f.read(4))[0]

            for i in range(count):
                vec = np.frombuffer(f.read(self.DIMENSION), dtype=dt)
                if astype is not None:
                    self.VECTORS.append(vec.astype(astype))
                else:
                    self.VECTORS.append(vec)

    @staticmethod
    def cos_dist(x, y):
        return -np.dot(x, y) # / (np.sqrt(np.dot(x, x)) * np.sqrt(np.dot(y, y)))

    @staticmethod
    def l2_dist(x, y):
        dxy = x - y
        return np.sqrt(np.dot(dxy, dxy))

    def get_distance_vector(self, query_image_index):
        rank = np.zeros(len(self.VECTORS))

        for i in range(len(self.VECTORS)):
            rank[i] = self.cos_dist(self.VECTORS[query_image_index].astype(np.float32), self.VECTORS[i].astype(np.float32))
        return rank

    def get_rank(self, query_image_index, searched_image_index):
        if not isinstance(searched_image_index, list):
            searched_image_index = [searched_image_index]

        if not isinstance(query_image_index, list):
            query_image_index = [query_image_index]

        rank_vec = np.zeros(len(self.VECTORS))
        for index in query_image_index:
            rank_vec += self.get_distance_vector(index)

        index_vec = np.argsort(rank_vec)
        ret_list = []
        ret_distances = []

        for index in searched_image_index:
            ret_distances.append(abs(rank_vec[index] - rank_vec[index_vec[0]]))
            # print("distance to first " + str(rank_vec[index] - rank_vec[index_vec[0]]))
            # print("distance to last " + str(rank_vec[index] - rank_vec[index_vec[len(index_vec) - 1]]))

            array_of_indexes = np.where(index_vec == index)[0]
            if len(array_of_indexes) != 1:
                raise Exception("Image ID " + index + " not found in array_of_indexes")
            ret_list.append(array_of_indexes[0])

        if len(ret_list) == 1:
            return ret_list[0], ret_distances[0], index_vec
        return ret_list, ret_distances, index_vec

    def _get_best_rank(self, image_indexes, searched_image_index, sim_settings, n_reranks = 1):
        if max(sim_settings.N_RERANKS) < n_reranks:
            return []

        distances = []
        for index in image_indexes[:sim_settings.DISPLAY_SIZE]:
            dist = self.cos_dist(self.VECTORS[index].astype(np.float32), self.VECTORS[searched_image_index].astype(np.float32))
            distances.append(dist)
        best_ranks = [image_indexes[i] for i in np.argsort(distances)[:sim_settings.N_CLOSEST]]

        searched_image_rank, searched_image_distance, rank_vector = self.get_rank(best_ranks, searched_image_index)

        simulation_utils.SimilarityVisualization().new_iteration(rank_vector[0], text=[
            "S " + str(searched_image_rank), "d=" + str(searched_image_distance)
        ])

        if searched_image_distance > 0:
            l = self._get_best_rank(rank_vector, searched_image_index, sim_settings, n_reranks + 1)
            for rerank in sim_settings.N_RERANKS:
                if rerank == n_reranks:
                    l.append((n_reranks, searched_image_rank))
        else:
            l = []
            for rerank in sim_settings.N_RERANKS:
                if rerank >= n_reranks:
                    l.append((rerank, searched_image_rank))
        return l

    def get_best_rank(self, image_indexes, searched_image_index, sim_settings):
        ranks = {}
        for disp_size in sim_settings.DISPLAY_SIZE:
            for n_closest in sim_settings.N_CLOSEST:
                sim = SimilaritySettings()
                sim.DISPLAY_SIZE = disp_size
                sim.N_CLOSEST = n_closest
                sim.N_RERANKS = sim_settings.N_RERANKS

                results = self._get_best_rank(image_indexes, searched_image_index, sim)
                for reranks, image_rank in results:
                    ranks[str(disp_size) + ":" + str(n_closest) + " " + str(reranks) + "x"] = image_rank
        return ranks


class SimilaritySettings:
    N_CLOSEST = []
    DISPLAY_SIZE = []
    N_RERANKS = []
