import numpy as np
from simulations import simulation_utils, graph_utils
from common_utils import console
import random


class Distance:

    def __init__(self):
        self._ranks = {}
        self._similarity = simulation_utils.Similarity()

    def read_vectors(self, filename):
        self._similarity.read_vectors(filename, astype=np.float32)

    def distances(self, sample_size):
        pt = console.ProgressTracker()
        pt.info(">> Calculating distances...")

        if sample_size is None:
            samples = range(len(self._similarity.VECTORS))
        else:
            samples = [random.randint(0, len(self._similarity.VECTORS) - 1) for _ in range(sample_size)]

        pt.reset(len(samples) * (len(samples) - 1) / 2)

        dists = []
        for i in range(len(samples)):
            for j in range(i + 1, len(samples)):
                dist = simulation_utils.Similarity.cos_dist(
                    self._similarity.VECTORS[samples[i]], self._similarity.VECTORS[samples[j]])
                dists.append(dist)
            pt.increment(len(samples) - (i+1))

        dists.sort()
        pt.info("\t> Min dist: " + str(dists[0]))
        pt.info("\t> Max dist: " + str(dists[-1]))

        self._ranks["$\cos$ distance"] = dists
        return dists

    def graph(self, graph_filename):
        graph_utils.plot_histogram(self._ranks, 200, graph_filename, title='Distance')
        graph_utils.plot_accumulative(self._ranks, graph_filename+"-accum", title='Distance')


a = Distance()
a.read_vectors("C:\\Users\\Tom\\Workspace\\ViretTool\\TestData\\TRECVid\\TRECVid.vector")
d = a.distances(3000)
a.graph("C:\\Users\\Tom\\Workspace\\KeywordSearch\\tensorflow\\text\\cos_distance-VGG_Vectors")

