import sys
import argparse
import numpy as np
from simulations import simulation_utils, similarity, visualization, user_queries
from common_utils import console, graph_utils
import random
import pickle
import os
from common_utils.dataset import VBS2018_HEADER
HEADER = VBS2018_HEADER


class Simulation:
    """
    """

    def __init__(self):
        """

        """
        self._images = None
        self._ranks = {}
        self._idf = None
        self.use_byte = False
        self._visualization = None
        self.samples = []
        self.indexes = []
        self._similarity = None
        self._similarity_settings = None
        self.thresholds = [None]

    def read_keyword(self, filename):
        self._images = simulation_utils.Keywords()
        self._images.read_images(filename, HEADER)

    # region Sample & index generation

    def gen_samples(self, filename, sample_size, max_query_len, distribution=None):
        """
        Loads samples and indexes from a file.
        Generates samples and indexes if file does not exist.

        Args:
            filename: pickle file to load samples and indexes from.
            sample_size: number of samples to generate.
            max_query_len: number of indexes to generate for each sample.
            distribution: custom probability distribution vector.
        """
        pt = console.ProgressTracker()

        filename += '-samples.pickle'

        if os.path.isfile(filename):
            pt.info(">> Restoring samples...")
            with open(filename, 'rb') as f:
                (self.samples, self.indexes) = pickle.load(f)
            return

        if self._images is None:
            pt.error('Missing image keyword vectors to generate samples.')
            exit(1)
        pt.info(">> Generating samples...")
        self.samples = [random.randint(0, len(self._images) - 1) for _ in range(sample_size)]
        self.__gen_indexes(max_query_len, distribution)

        with open(filename, 'wb') as f:
            pickle.dump((self.samples, self.indexes), f)

    def __gen_indexes(self, max_query_len, distribution):
        """
        Generates indexes for all samples from a distribution
        by generating i-th best index of images' distribution based on a given distribution.

        Args:
            max_query_len: number of indexes to generate.
            distribution: probability distribution vector.
                          If none, indexes are generated directly from images' distribution.
        """
        pt = console.ProgressTracker()
        pt.info(">> Generating random indexes for samples...")
        self.indexes = []

        for index in self.samples:
            image = self._images[index]
            dist = image.DISTRIBUTION if distribution is None else distribution

            rand_indexes = []
            while len(rand_indexes) < max_query_len:
                rand = simulation_utils.get_random_index_from_dist(dist)
                if rand not in rand_indexes:
                    rand_indexes.append(rand)

            if distribution is not None:
                cls_indexes = np.argsort(image.DISTRIBUTION)[::-1]
                self.indexes.append([cls_indexes[i] for i in rand_indexes])
            else:
                self.indexes.append(rand_indexes)

        # lmbda=0.004
        # pt.info(">> Generating indexes from exponential distribution for samples...")
        # pt.info("\t> Lambda: " + str(lmbda))
        #
        # exp = np.arange(1, self._images.DIMENSION + 1)
        # exp = lmbda * np.exp(-lmbda * exp)
        # exp = exp / np.sum(exp)

    # endregion

    # region Modifiers

    def use_idf(self, unnormalized_mean_filename):
        """
        Use inverted document frequency technique.

        Args:
            unnormalized_mean_filename: a location of unnormalized mean file.
        """
        pt = console.ProgressTracker()
        pt.info(">> Computing IDF...")

        self._idf = simulation_utils.IDF()
        self._idf.read_term_count(unnormalized_mean_filename, HEADER)
        self._idf.compute_idf()

    def use_similarity(self, filename, disp_size, n_closest, n_reranks):
        """
        Use similarity reranking.

        Args:
            filename: a location of similarity vector file.
            disp_size: a list - display size to use.
            n_closest: a list - number of closest images to use when reranking.
            n_reranks: a list - number of similarity reranks to perform.
        """
        self._similarity_settings = similarity.SimilaritySettings(
            disp_size, n_closest, n_reranks
        )
        self._similarity = similarity.Similarity()
        self._similarity.read_vectors(filename, val_type=np.int8)

    def use_visualization(self, image_dir, filename, no_iterations, no_images):
        filename += '-visualization'
        self._visualization = visualization.SimilarityVisualization(filename, [120, 90], no_images,
                                                                    no_iterations, image_dir)

    def restore_ranks(self, filename):
        """
        Restore ranks from previous runs to use them in graph.

        Args:
            filename: a location of ranks pickle file.
        """
        pt = console.ProgressTracker()
        pt.info(">> Restoring ranks...")

        filename += '-ranks.pickle'

        if not os.path.isfile(filename):
            pt.info("\t> Filename " + filename + " does not exist, ranks cannot be restored.")
            return

        with open(filename, 'rb') as f:
            r = pickle.load(f)
            for k in r.keys():
                self._ranks[k] = r[k]

    def save_ranks(self, filename):
        """
        Restore ranks from previous runs to use them in graph.

        Args:
            filename: a location of ranks pickle file.
        """
        pt = console.ProgressTracker()
        pt.info(">> Saving ranks...")

        filename += '-ranks.pickle'

        with open(filename, 'wb') as f:
            pickle.dump(self._ranks, f)

    # endregion

    # region Image ranking

    @staticmethod
    def _get_rank_of_image(image_id, array):
        """
        Calculates rank of an image in an array.

        Args:
            image_id:
            array: array of distances.
        Returns:
            A tuple.
            A rank of an image.
            Sorted indexes by array value.
        """
        indexes = np.argsort(array)[::-1]
        array_of_indexes = np.where(indexes == image_id)[0]

        if len(array_of_indexes) != 1:
            raise Exception("Image ID " + image_id + " not found in array_of_indexes")
        return array_of_indexes[0] + 1, indexes

    def rank(self, query_length_list):
        """

        Args:
            query_length_list:
        """
        pt = console.ProgressTracker()

        if self.use_byte:
            pt.info(">> Converting probabilities from floats to bytes...")
            pt.reset(len(self._images.CLASSES))

            nonzero = 0
            for cls_index in range(len(self._images.CLASSES)):
                self._images.CLASSES[cls_index] = np.round(self._images.CLASSES[cls_index] * 255)

                nonzero += np.sum(self._images.CLASSES[cls_index] > 0)
                if cls_index % 10 == 9: pt.increment(10)
            pt.info("\t> Nonzero classes on average: " + str(nonzero / len(self._images.CLASSES[0])))

        for threshold in self.thresholds:
            if threshold is not None:
                pt.info(">> Updating threshold to " + str(threshold) + "...")
                pt.reset(len(self._images.CLASSES))

                if self.use_byte:
                    threshold *= 255

                nonzero = 0
                for cls_index in range(len(self._images.CLASSES)):
                    nullable = self._images.CLASSES[cls_index] < threshold
                    nonzero += len(self._images.CLASSES[cls_index]) - np.sum(nullable)

                    self._images.CLASSES[cls_index][nullable] = 0
                    pt.increment()
                pt.info("\t> Nonzero classes on average: " + str(nonzero / len(self._images.CLASSES[0])))

            pt.info(">> Calculating image ranks...")
            pt.reset(len(self.samples))

            rank_str = ('usr' if query_length_list is None else 'sim') + ' ' + \
                       ('byte' if self.use_byte else '') + ' ' + str(threshold)

            for image_id, indexes in zip(self.samples, self.indexes):
                if query_length_list is None:
                    self._rank_image(image_id, indexes, False, rank_str)
                    if self._idf is not None:
                        self._rank_image(image_id, indexes, True, rank_str + ' idf')
                else:
                    for query_length in query_length_list:
                        self._rank_image(image_id, indexes[:query_length], False, rank_str + ' ' + str(query_length))
                        if self._idf is not None and query_length > 1:
                            self._rank_image(image_id, indexes[:query_length], True,
                                             rank_str + ' ' + str(query_length) + ' idf')
                pt.increment()

        if self._visualization is not None:
            self._visualization.save()
        pt.info(">> Image ranks calculated.")

    def _rank_image(self, image_id, selected_indexes, use_idf, plot_name):
        """

        Args:
            image_id:
            selected_indexes:
            use_idf:
            plot_name:
        """
        rank, sim_rank = None, None

        if len(selected_indexes) > 0:
            array = np.copy(self._images.CLASSES[selected_indexes[0]])

            if len(selected_indexes) > 1:
                if use_idf:
                    array = self._idf.IDF[selected_indexes[0]] * self._images.CLASSES[selected_indexes[0]]

                for i in range(1, len(selected_indexes)):
                    array += self._images.CLASSES[selected_indexes[i]] \
                        if not use_idf \
                        else self._idf.IDF[selected_indexes[i]] * self._images.CLASSES[selected_indexes[i]]

            if array[image_id] != 0:
                rank, indexes = self._get_rank_of_image(image_id, array)

                if self._visualization is not None:
                    self._visualization.new_image(plot_name, image_id)
                    self._visualization.new_iteration(indexes[0], text="K " + str(rank))

                if self._similarity is not None:
                    sim_rank = self._similarity.get_best_rank(indexes, image_id, self._similarity_settings,
                                                              self._visualization)

        if plot_name not in self._ranks:
            self._ranks[plot_name] = []
        self._ranks[plot_name].append(rank)

        if self._similarity is not None:
            if sim_rank is None:
                sim_rank = self._similarity_settings.get_empty_configurations()

            for key in sim_rank.keys():
                if plot_name + " " + key not in self._ranks:
                    self._ranks[plot_name + " " + key] = []
                self._ranks[plot_name + " " + key].append(sim_rank[key])

    # endregion

    def distribution_from_indexes(self, filename):
        if os.path.exists(filename + '-distribution.pickle'):
            pt = console.ProgressTracker()
            pt.info(">> Restoring distribution from {}-distribution.pickle".format(filename))

            with open(filename + '-distribution.pickle', 'rb') as f:
                return pickle.load(f)

        dist = np.zeros(self._images.NO_CLASSES)

        for image_id, user_indexes in zip(self.samples, self.indexes):
            image = self._images[image_id]
            indexes = np.argsort(image.DISTRIBUTION)[::-1]

            for i in range(self._images.NO_CLASSES):
                if indexes[i] in user_indexes:
                    dist[i] += 1

        smoothed = np.zeros(self._images.NO_CLASSES)
        for i in range(self._images.NO_CLASSES):
            for j in range(max(0, i-10), min(i+10, self._images.NO_CLASSES)):
                smoothed[i] += dist[j]
            smoothed[i] /= min(i+10, self._images.NO_CLASSES) - max(0, i-10)

        min_reached = smoothed[0]
        accumulated = 0.0
        for i in range(1, self._images.NO_CLASSES):
            if min_reached < smoothed[i]:
                accumulated += smoothed[i] - min_reached
                smoothed[i] = min_reached
            elif smoothed[i] + accumulated > min_reached:
                accumulated -= min_reached - smoothed[i]
                smoothed[i] = min_reached
            else:
                smoothed[i] += accumulated
                accumulated = 0
                min_reached = smoothed[i]

        smoothed /= np.sum(smoothed)

        with open(filename + '-distribution-raw.pickle', 'wb') as f:
            pickle.dump(dist, f)
        with open(filename + '-distribution.pickle', 'wb') as f:
            pickle.dump(smoothed, f)

        return smoothed

    def histogram_of_hits(self, graph_filename):
        """

        Args:
            graph_filename:
        """
        pt = console.ProgressTracker()
        pt.info(">> Calculating histogram of hits...")

        h, h_rand, t, t_rand = [], [], [], []

        for index, user_indexes in zip(self.samples, self.indexes):
            image = self._images[index]
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
                                            self._images.NO_CLASSES, graph_filename, title='Hits')

    def graph(self, filename):
        """
        Plot ranks.

        Args:
            filename: a location where to store a graph.
        """
        graph_utils.plot_accumulative(self._ranks, filename, title='Cumulative Rank', x_axis='Rank',
                                      y_axis='Number of Images [%]', viewbox=[(-100, 20100), (-2, 102)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # common
    parser.add_argument('--keyword', type=str, default=False, help='keyword vector filename')

    parser.add_argument('--byte', action='store_true', default=False,
                        help='convert keyword vectors to byte representation')
    parser.add_argument('--idf', type=str, default=False, help='unnormalized mean filename if IDF should be used')
    parser.add_argument('--thresholds', type=str, default=False,
                        help='ignore indexes with values smaller than threshold, multiple thresholds divided by comma, '
                             'default \'None\' for no threshold')

    # similarity
    parser.add_argument('--similarity', type=str, default=False,
                        help='similarity vector filename if similarity reranking should be used')
    parser.add_argument('--disp_size', type=str, default=False)
    parser.add_argument('--n_closest', type=str, default=False)
    parser.add_argument('--n_reranks', type=str, default=False)

    #
    parser.add_argument('--filename', type=str, default=False,
                        help='common filename used for storing and restoring samples, rankings and visualization')
    parser.add_argument('--visualization', type=str, default=False,
                        help='location of images if visualization should be used')
    parser.add_argument('--restore_ranks', action='store_true', default=False, help='restore ranks from filename')

    #
    parser.add_argument('--gen_samples', type=int, default=False, help='number of samples to generate')
    parser.add_argument('--query_lengths', type=str, default=False, help='query lengths')

    parser.add_argument('--label_file', type=str, default=False)
    parser.add_argument('--log_file', type=str, default=False)
    parser.add_argument('--rank', action='store_true', default=False)
    parser.add_argument('--use_user_dist', action='store_true', default=False)

    parser.add_argument('--graph', action='store_true', default=False)
    # parser.add_argument('--hist', type=str, default=None)
    args = parser.parse_args()

    # read_queries
    #   'C:\\Users\\Tom\\Documents\\Visual Studio 2017\\Projects\\KeywordSelector\\' +
    #   'KeywordSelector\\bin\\Debug\\Log\\KeywordSelector_2017-12-04_14-35-45.txt'
    # read_labels
    #   'C:\\Users\\Tom\\Workspace\\ViretTool\\TestData\\TRECVid\\TRECVid-GoogLeNet.label'

    if len(sys.argv) == 1:
        parser.print_help()
        exit(1)

    pt = console.ProgressTracker()

    u = Simulation()

    if args.byte:
        u.use_byte = True

    if args.idf:
        u.use_idf(args.idf)

    if args.thresholds:
        u.thresholds = [None if i == "None" else float(i) for i in args.thresholds.split(',')]
        u.thresholds.sort(key=lambda x: -1 if x is None else x)

    if args.restore_ranks:
        if not args.filename:
            pt.error('\'filename\' must be specified to restore rankings.')
            exit(1)
        u.restore_ranks(args.filename)

    if args.label_file and args.log_file:
        u.samples, u.indexes = user_queries.parse_queries(args.log_file, args.label_file)

    if args.keyword:
        u.read_keyword(args.keyword)

    if args.gen_samples:
        if not args.filename or not args.query_lengths:
            pt.error('\'filename\' and \'query_lengths\' must be specified to create or restore generated samples.')
            exit(1)
        if args.use_user_dist:  # and not (args.label_file and args.log_file):
                pt.info('\t> \'label_file\' and \'log_file\' must be specified to generate custom user distribution '
                        'if distribution file does not exist.')
        u.gen_samples(args.filename, args.gen_samples,
                      max([int(i) for i in args.query_lengths.split(',')]),
                      u.distribution_from_indexes(args.filename) if args.use_user_dist else None)

    if args.visualization:
        if not args.filename or not args.n_reranks:
            pt.error('\'filename\' and \'n_reranks\' must be specified to use visualization.')
            exit(1)
        u.use_visualization(args.visualization, args.filename, max([int(i) for i in args.n_reranks.split(',')]) + 2,
                            min(200, len(u.samples)))

    if args.similarity:
        if not (args.disp_size and args.n_closest and args.n_reranks):
            pt.error('\'disp_size\', \'n_closest\' and \'n_reranks\' must be specified to use similarity reranking.')
            exit(1)

        u.use_similarity(args.similarity,
                         [int(i) for i in args.disp_size.split(',')],
                         [int(i) for i in args.n_closest.split(',')],
                         [int(i) for i in args.n_reranks.split(',')])

    if args.rank:
        if not args.keyword or len(u.samples) == 0:
            pt.error('\'keyword\' and samples must be specified to rank.')
            exit(1)
        u.rank([int(i) for i in args.query_lengths.split(',')] if args.query_lengths else None)

        if args.filename:
            u.save_ranks(args.filename)

    if args.graph:
        if not args.filename:
            pt.error('\'filename\' must be specified to graph rankings.')
            exit(1)
        u.graph(args.filename)

    # if args.hist is not None:
    #     u.histogram_of_hits(args.hist)

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


# python simulations/simulation.py --keyword=C:\Users\Tom\Workspace\KeywordSearch\tensorflow\preparation\bin\LSC2018Dataset.softmax --idf=C:\Users\Tom\Workspace\KeywordSearch\tensorflow\preparation\bin\LSC2018Dataset.sumX --th
# resholds=None,0.001,0.01 --gen_samples=100 --query_lengths=4 --label_file=C:\Users\Tom\Workspace\ViretTool\TestData\LSC2018\LSC2018-GoogLeNet.label --log_file="C:\Users\Tom\Documents\Visual Studio 2017\Projects\KeywordSelector\KeywordSelector\bin\Debug\Log\KeywordSelector
# _2017-12-04_14-35-45.txt" --use_user_dist --rank --graph --filename=LSC2018Dataset-usersim-idf-threshold


# python preparation/classify.py --image_dir="E:\VIRET\Keyframes" --num_classes=1390 --model_path=C:\Users\Tom\Workspace\KeywordSearch\tensorflow\bin\checkpoints\model_v1.ckpt-280000 --run_name=TRECVidOldKeyframes
