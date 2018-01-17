import argparse
import numpy as np
from simulations import simulation_utils, graph_utils
from common_utils import console
import random
import pickle


class UserSimulation:

    def __init__(self):
        self._images = simulation_utils.Images()
        self._idf = simulation_utils.IDF()
        self._ranks = {}
        self._samples = []
        self._indexes = []
        self._labels = dict()
        self._similarity = simulation_utils.Similarity()

    @staticmethod
    def _read_queries(filename):
        queries = []
        no_keyword, not_recognized = 0, 0

        def process_query(lines):
            if len(lines) >= 3:
                frame_id = int(lines[0].split(';')[0].split(':')[1])
                if lines[2].startswith("Query:"):
                    return frame_id, [
                        (int(or_part.split(',')[0]), int(or_part.split(',')[1]) == 1)
                        for or_part in lines[2].split(':')[1].split('or')
                    ]
                elif lines[2].startswith("Keyword"):
                    return frame_id, []
            return None, None

        with open(filename, 'r') as f:
            lines = []
            for line in f:
                if line[0] == '#' or line == "--- QUERY ---\n":
                    continue
                if line == "--- END ---\n":
                    frame_id, query = process_query(lines)
                    if frame_id is None:
                        not_recognized += 1
                        lines.clear()
                        continue

                    if len(query) == 0:
                        no_keyword += 1
                    queries.append((frame_id, query))
                    lines.clear()
                    continue

                lines.append(line)
        return queries

    def parse_queries(self, query_log_filename, label_filename):
        pt = console.ProgressTracker()
        pt.info(">> Parsing queries...")

        self._labels = simulation_utils.Label.read_labels(label_filename)
        self._samples = []
        self._indexes = []
        queries = self._read_queries(query_log_filename)

        for frame_id, query in queries:
            self._samples.append(frame_id)
            self._indexes.append(simulation_utils.Label.expand_query(self._labels, query))

    def read_similarity(self, filename):
        self._similarity.read_vectors(filename)

    def read_images(self, images_filename):
        self._images.read_images(images_filename)

    def invert_index(self, images_filename):
        self._images.invert_index(images_filename + "-inverted")

    def compute_idf(self, unnormalized_mean_filename):
        pt = console.ProgressTracker()
        pt.info(">> Computing IDF...")

        self._idf.read_term_count(unnormalized_mean_filename)
        self._idf.compute_idf()

    def gen_samples(self, sample_size):
        pt = console.ProgressTracker()
        pt.info(">> Generating samples...")

        self._samples = [random.randint(0, len(self._images.IMAGES) - 1) for _ in range(sample_size)]

    @staticmethod
    def _get_rank_of_image(image, array):
        indexes = np.argsort(array)[::-1]
        for i in range(len(indexes)):
            if indexes[i] == image.ID:
                return i + 1, indexes

    def save(self, filename):
        pt = console.ProgressTracker()
        pt.info(">> Saving ranks and samples...")

        with open(filename + '_ranks.pickle', 'wb') as f:
            pickle.dump(self._ranks, f)
        with open(filename + '_samples.pickle', 'wb') as f:
            pickle.dump((self._samples, self._indexes), f)

    def restore_ranks(self, filename):
        pt = console.ProgressTracker()
        pt.info(">> Restoring ranks...")

        with open(filename + '_ranks.pickle', 'rb') as f:
            r = pickle.load(f)
            for k in r.keys():
                self._ranks[k] = r[k]

    def restore_samples(self, filename):
        pt = console.ProgressTracker()
        pt.info(">> Restoring samples...")

        with open(filename + '_samples.pickle', 'rb') as f:
            (self._samples, self._indexes) = pickle.load(f)

    def graph(self, graph_filename):
        graph_utils.plot_accumulative(self._ranks, graph_filename, title='Cumulative Rank')

    def _rank(self, threshold_list, query_length_list, use_idf, byte_representation, similarity):
        pt = console.ProgressTracker()

        if byte_representation:
            pt.info(">> Converting probabilities from floats to bytes...")
            pt.reset(len(self._images.CLASSES))

            nonzero = 0
            for cls_index in range(len(self._images.CLASSES)):
                self._images.CLASSES[cls_index] = np.round(self._images.CLASSES[cls_index] * 255)

                nonzero += np.sum(self._images.CLASSES[cls_index] > 0)
                pt.increment()
            pt.info("\t> Nonzero classes on average: " + str(nonzero / len(self._images.CLASSES[0])))

        for threshold in threshold_list:
            if threshold is not None:
                pt.info(">> Updating threshold to " + str(threshold) + "...")
                pt.reset(len(self._images.CLASSES))

                nonzero = 0
                for cls_index in range(len(self._images.CLASSES)):
                    if byte_representation:
                        nullable = self._images.CLASSES[cls_index] < (threshold * 255)
                    else:
                        nullable = self._images.CLASSES[cls_index] < threshold
                    nonzero += len(self._images.CLASSES[cls_index]) - np.sum(nullable)

                    self._images.CLASSES[cls_index][nullable] = 0
                    pt.increment()
                pt.info("\t> Nonzero classes on average: " + str(nonzero / len(self._images.CLASSES[0])))

            pt.info(">> Calculating image ranks...")
            pt.reset(len(self._samples))

            byte_str = "byte " if byte_representation else ""
            for index, rand_indexes in zip(self._samples, self._indexes):
                image = self._images.IMAGES[index]

                if query_length_list is None:
                    self._rank_image(image, rand_indexes, False, similarity,
                                     'user ' + byte_str + str(threshold))
                    if use_idf:
                        self._rank_image(image, rand_indexes, True, similarity,
                                         'user idf ' + byte_str + str(threshold))
                else:
                    for query_length in query_length_list:
                        self._rank_image(image, rand_indexes[:query_length], False, similarity,
                                         'uniform ' + byte_str + str(query_length) + ' ' + str(threshold))
                        if use_idf and query_length > 1:
                            self._rank_image(image, rand_indexes[:query_length], True, similarity,
                                             'idf ' + byte_str + str(query_length) + ' ' + str(threshold))
                pt.increment()

    def _rank_image(self, image, selected_indexes, use_idf, similarity, plot_name):
        rank, sim_rank = None, None

        if len(selected_indexes) > 0:
            array = self._images.CLASSES[selected_indexes[0]]

            if len(selected_indexes) > 1:
                array = self._images.CLASSES[selected_indexes[0]] + self._images.CLASSES[selected_indexes[1]] \
                    if not use_idf else self._idf.IDF[selected_indexes[0]] * self._images.CLASSES[selected_indexes[0]] + \
                                        self._idf.IDF[selected_indexes[1]] * self._images.CLASSES[selected_indexes[1]]

                i = 2
                while i < len(selected_indexes):
                    array += self._images.CLASSES[selected_indexes[i]] \
                        if not use_idf else self._idf.IDF[selected_indexes[i]] * self._images.CLASSES[selected_indexes[i]]
                    i += 1

            if array[image.ID] != 0:
                rank, indexes = self._get_rank_of_image(image, array)
                if similarity is not None:
                    sim_rank = self._similarity.get_best_rank(indexes, image.ID, similarity)

        if plot_name in self._ranks:
            self._ranks[plot_name].append(rank)
        else:
            self._ranks[plot_name] = [rank]

        if similarity is not None:
            if sim_rank is not None:
                for key in sim_rank.keys():
                    if plot_name + " " + key not in self._ranks:
                        self._ranks[plot_name + " " + key] = []
                    self._ranks[plot_name + " " + key].append(sim_rank[key])
            else:
                for disp_size, n_closest, reranks in zip(similarity.DISPLAY_SIZE, similarity.N_CLOSEST, similarity.N_RERANKS):
                    p_name = plot_name + " " + str(disp_size) + ":" + str(n_closest) + " " + str(reranks) + "x"
                    if p_name not in self._ranks:
                        self._ranks[p_name] = []
                    self._ranks[p_name].append(None)

    def histogram_of_hits(self, graph_filename):
        pt = console.ProgressTracker()
        pt.info(">> Calculating histogram of hits...")

        h, h_rand, t, t_rand = [], [], [], []

        for index, user_indexes in zip(self._samples, self._indexes):
            image = self._images.IMAGES[index]
            indexes = np.argsort(image.DISTRIBUTION)

            rand_indexes = []
            while len(rand_indexes) < 5:
                rand = simulation_utils.get_random_index_from_dist(image.DISTRIBUTION)
                if rand not in rand_indexes:
                    rand_indexes.append(rand)

            hits_rand = []
            top_rand = True
            hits = []
            top = True
            for i in reversed(range(len(indexes))):
                if indexes[i] in rand_indexes:
                    if top_rand:
                        top_rand = False
                        t_rand.append(len(indexes) - i)
                    hits_rand.append(len(indexes) - i)
                if indexes[i] in user_indexes:
                    if top:
                        top = False
                        t.append(len(indexes) - i)
                    hits.append(len(indexes) - i)
            h.extend(hits)
            h_rand.extend(hits_rand)
        graph_utils.plot_discrete_histogram({'hits': h, 'top hits': t, 'hits rand': h_rand, 'top hits rand': t_rand},
                                            self._images.DIMENSION, graph_filename, title='Hits')

    def _gen_indexes(self, query_length):
        pt = console.ProgressTracker()
        pt.info(">> Generating random indexes for samples...")
        self._indexes = []

        for index in self._samples:
            image = self._images.IMAGES[index]

            rand_indexes = []
            while len(rand_indexes) < query_length:
                rand = simulation_utils.get_random_index_from_dist(image.DISTRIBUTION)
                if rand not in rand_indexes:
                    rand_indexes.append(rand)
            self._indexes.append(rand_indexes)

    def rank(self, threshold_list,  query_length_list, use_idf=False, byte_representation=False, similarity=None):
        if len(self._indexes) == 0:
            self._gen_indexes(max(query_length_list))
        self._rank(threshold_list, query_length_list, use_idf, byte_representation, similarity)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # common
    parser.add_argument('-i', type=str, default=False)
    parser.add_argument('-u', type=str, default=False)
    parser.add_argument('-g', type=str, default=False)
    parser.add_argument('-s', type=str, default=False)
    parser.add_argument('--rank', action='store_true', default=False)
    parser.add_argument('--idf', action='store_true', default=False)
    parser.add_argument('--byte', action='store_true', default=False)
    parser.add_argument('--similarity', type=str, default=False)
    parser.add_argument('--sim_closest', type=str, default="")
    parser.add_argument('--sim_disp_size', type=str, default="")
    parser.add_argument('--sim_reranks', type=str, default="")
    # perfect
    parser.add_argument('--sample_size', type=int, default=False)
    parser.add_argument('--thresholds', type=str, default=None)
    parser.add_argument('--query_lengths', type=str, default=None)
    parser.add_argument('--restore_ranks', type=str, default=False)
    parser.add_argument('--restore_samples', type=str, default=False)
    # human
    parser.add_argument('--label_file', type=str, default=None)
    parser.add_argument('--log_file', type=str, default=None)
    parser.add_argument('--hist', type=str, default=None)
    args = parser.parse_args()

    # read_queries
    #   'C:\\Users\\Tom\\Documents\\Visual Studio 2017\\Projects\\KeywordSelector\\' +
    #   'KeywordSelector\\bin\\Debug\\Log\\KeywordSelector_2017-12-04_14-35-45.txt'
    # read_labels
    #   'C:\\Users\\Tom\\Workspace\\ViretTool\\TestData\\TRECVid\\TRECVid-GoogLeNet.label'

    u = UserSimulation()
    if args.i:
        u.read_images(args.i)
    if args.u:
        u.compute_idf(args.u)
    if args.similarity:
        u.read_similarity(args.similarity)

    if args.restore_samples:
        u.restore_samples(args.restore_samples)

    elif args.sample_size:
        u.gen_samples(args.sample_size)

    if args.label_file is not None and args.log_file is not None:
        u.parse_queries(args.log_file, args.label_file)

    if args.restore_ranks:
        u.restore_ranks(args.restore_ranks)

    if args.rank and args.thresholds is not None and args.i:
        u.invert_index(args.i)

        sim = None
        if args.similarity:
            sim = simulation_utils.SimilaritySettings()
            sim.N_CLOSEST = [int(i) for i in args.sim_closest.split(',')]
            sim.DISPLAY_SIZE = [int(i) for i in args.sim_disp_size.split(',')]
            sim.N_RERANKS = [int(i) for i in args.sim_reranks.split(',')]

        u.rank([None if i == "None" else float(i) for i in args.thresholds.split(',')],
               None if args.query_lengths is None else [int(i) for i in args.query_lengths.split(',')],
               use_idf=args.idf, byte_representation=args.byte, similarity=sim)

    if args.s:
        u.save(args.s)

    if args.g:
        u.graph(args.g)

    if args.hist is not None:
        u.histogram_of_hits(args.hist)

# histogram of user hits
# py simulations/simulation.py --human_user
# --hist=C:\Users\Tom\Workspace\KeywordSearch\tensorflow\text\rank_TrecVidKF-Test.hist
# --log_file="C:\Users\Tom\Documents\Visual Studio 2017\Projects\KeywordSelector\KeywordSelector\bin\Debug\Log\
#   KeywordSelector_2017-12-04_14-35-45.txt"
# --label_file=C:\Users\Tom\Workspace\ViretTool\TestData\TRECVid\TRECVid-GoogLeNet.label
# -i=C:\Users\Tom\Workspace\KeywordSearch\tensorflow\bin\TrecVidKF.softmax

# run simulation
# py simulations/simulation.py
#   --perfect_user
#   -i=C:\Users\Tom\Workspace\KeywordSearch\tensorflow\bin\TrecVidKF-Test.softmax
#   -u=C:\Users\Tom\Workspace\KeywordSearch\tensorflow\bin\covariance\mean_unorm-TrecVidKF-Test.bin
#   -g=C:\Users\Tom\Workspace\KeywordSearch\tensorflow\text\rank_TrecVidKF-Test
#   --sample_size=1000
#   --query_lengths=1,2,3,4,5
#   --save=C:\Users\Tom\Workspace\KeywordSearch\tensorflow\text\rank_TrecVidKF-Test

# draw graph
# py simulations/simulation.py
#   --perfect_user
#   -g=C:\Users\Tom\Workspace\KeywordSearch\tensorflow\text\rank_TrecVidKF-Test
#   --restore_ranks=C:\Users\Tom\Workspace\KeywordSearch\tensorflow\text\rank_TrecVidKF-Test



# --rank -i=C:\Users\Tom\Workspace\KeywordSearch\tensorflow\bin\TrecVidKF.softmax -u=C:\Users\Tom\Workspace\KeywordSearch\tensorflow\bin\covariance\mean_unorm-TrecVidKF.bin -g=C:\Users\Tom\Workspace\KeywordSearch\tensorflow\text\rank_TrecVidKF-SimilarityHumanComplex -s=C:\Users\Tom\Workspace\KeywordSearch\tensorflow\text\rank_TrecVidKF-SimilarityHumanComplex --thresholds=None --log_file="C:\Users\Tom\Documents\Visual Studio 2017\Projects\KeywordSelector\KeywordSelector\bin\Debug\Log\KeywordSelector_2017-12-04_14-35-45.txt" --label_file="C:\Users\Tom\Workspace\ViretTool\TestData\TRECVid\TRECVid-GoogLeNet.label" --similarity=C:\Users\Tom\Workspace\ViretTool\TestData\TRECVid\TRECVid.vector --sim_closest=1,2 --sim_disp_size=50,300 --sim_reranks=1,3