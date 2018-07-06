import numpy as np
from simulations import similarity
from common_utils import console, graph_utils
import random
import argparse


class Distance:
    """
    Computes distances between all vectors.
    """

    def __init__(self):
        self._ranks = {}
        self._similarity = similarity.Similarity()

    def read_vectors(self, filename):
        """
        Loads vectors from a file.

        Args:
            filename: vectors' filename.
        """
        self._similarity.read_vectors(filename)

    def distances(self, sample_size):
        """
        Computes distances between randomly selected vectors.

        Args:
            sample_size: number of vectors to select. If *None*, all vectors are selected.
        Returns:
            List of distances between all pairs of selected vectors.
        """
        pt = console.ProgressTracker()
        pt.info(">> Calculating distances...")

        if sample_size is None:
            samples = range(len(self._similarity.vectors))
        else:
            samples = [random.randint(0, len(self._similarity.vectors) - 1) for _ in range(sample_size)]

        pt.reset(len(samples) * (len(samples) - 1) / 2)

        dists = []
        for i in range(len(samples)):
            for j in range(i + 1, len(samples)):
                dist = similarity.cos_dist(
                    self._similarity.vectors[samples[i]], self._similarity.vectors[samples[j]]
                )
                dists.append(dist)
            pt.increment(len(samples) - (i+1))

        dists.sort()
        pt.info("\t> Min dist: " + str(dists[0]))
        pt.info("\t> Max dist: " + str(dists[-1]))

        self._ranks["$\cos$ distance"] = dists
        return dists

    def graph(self, graph_filename):
        """
        Plots histogram and accumulative graph of distances.

        Args:
            graph_filename: filename without extension,
        """
        graph_utils.plot_histogram(self._ranks, 200, graph_filename, title="Distance")
        graph_utils.plot_accumulative(self._ranks, graph_filename + "-accum", title="Distance")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vector_file", type=str, required=True)
    parser.add_argument("--out_graph_file", type=str, default=False)
    parser.add_argument("--sample_size", type=int, default=None)

    args = parser.parse_args()

    d = Distance()
    d.read_vectors(args.vector_file)
    d.distances(args.sample_size)
    if args.out_graph_file:
        d.graph(args.out_graph_file)
