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

    def read_images(self, images_filename):
        self._images.read_images(images_filename)

    def invert_index(self):
        self._images.invert_index()

    def read_mean(self, unnormalized_mean_filename):
        self._idf.read_term_count(unnormalized_mean_filename)
        self._idf.compute_idf()

    def gen_samples(self, sample_size):
        pt = console.ProgressTracker()
        pt.info(">> Generating samples...")

        self._samples = [random.randint(0, len(self._images.IMAGES) - 1) for _ in range(sample_size)]

    @staticmethod
    def _get_rank_of_image(image, array):
        indexes = np.argsort(array)
        for i in reversed(range(len(indexes))):
            if indexes[i] == image.ID:
                return len(indexes) - i

    def save(self, filename):
        pt = console.ProgressTracker()
        pt.info(">> Saving ranks and samples...")

        with open(filename + '_ranks.pickle', 'wb') as f:
            pickle.dump(self._ranks, f)
        with open(filename + '_samples.pickle', 'wb') as f:
            pickle.dump(self._samples, f)

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
            self._samples = pickle.load(f)

    def graph(self, graph_filename):
        d = dict()
        for key in self._ranks.keys():
            for key2 in self._ranks[key].keys():
                d[key + " " + str(key2)] = self._ranks[key][key2]

        graph_utils.plot_accumulative(d, graph_filename, title='Cumulative Rank')


class PerfectUserSimulation(UserSimulation):

    def __init__(self):
        super(PerfectUserSimulation, self).__init__()
        self._ranks = {
            'idf': {},
            'uniform': {}
        }

    def rank(self, query_length_list):
        pt = console.ProgressTracker()
        pt.reset(len(self._samples))
        pt.info(">> Calculating image ranks...")

        for query_length in query_length_list:
            if query_length != 1 and query_length not in self._ranks['idf']:
                self._ranks['idf'][query_length] = []
            if query_length not in self._ranks['uniform']:
                self._ranks['uniform'][query_length] = []

        for index in self._samples:
            for query_length in query_length_list:
                image = self._images.IMAGES[index]

                rand_indexes = []
                while len(rand_indexes) < query_length:
                    rand = simulation_utils.get_random_index_from_dist(image.DISTRIBUTION)
                    if rand not in rand_indexes:
                        rand_indexes.append(rand)

                if query_length == 1:
                    rank = self._get_rank_of_image(image, self._images.CLASSES[rand_indexes[0]])

                    self._ranks['uniform'][query_length].append(rank)
                elif query_length > 1:
                    array = self._images.CLASSES[rand_indexes[0]] + self._images.CLASSES[rand_indexes[1]]
                    i = 2
                    while i < query_length:
                        array += self._images.CLASSES[rand_indexes[i]]
                        i += 1
                    rank = self._get_rank_of_image(image, array)

                    self._ranks['uniform'][query_length].append(rank)

                    array = self._idf.IDF[rand_indexes[0]] * self._images.CLASSES[rand_indexes[0]] + \
                        self._idf.IDF[rand_indexes[1]] * self._images.CLASSES[rand_indexes[1]]
                    i = 2
                    while i < query_length:
                        array += self._idf.IDF[rand_indexes[i]] * self._images.CLASSES[rand_indexes[i]]
                        i += 1
                    rank = self._get_rank_of_image(image, array)

                    self._ranks['idf'][query_length].append(rank)

            pt.increment()


class HumanUserSimulation(UserSimulation):

    def __init__(self):
        super(HumanUserSimulation, self).__init__()
        self._indexes = []
        self._labels = dict()
        self._ranks = {
            'user': {}
        }

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
        self._labels = simulation_utils.Label.read_labels(label_filename)
        self._samples = []
        self._indexes = []
        queries = self._read_queries(query_log_filename)

        for frame_id, query in queries:
            self._samples.append(frame_id)
            self._indexes.append(simulation_utils.Label.expand_query(self._labels, query))

    def histogram_of_hits(self, graph_filename):
        pt = console.ProgressTracker()
        pt.info(">> Calculating histogram of hits...")

        h_rand = []
        t_rand = []
        h = []
        t = []
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
        graph_utils.plot_accumulative({'hits': h, 'top hits': t, 'hits rand': h_rand, 'top hits rand': t_rand}, graph_filename, title='Hits')

    def rank(self):
        pt = console.ProgressTracker()
        pt.reset(len(self._samples))
        pt.info(">> Calculating image ranks...")

        self._ranks['user']['uniform'] = []
        self._ranks['user']['idf'] = []

        for index, rand_indexes in zip(self._samples, self._indexes):
            image = self._images.IMAGES[index]

            if len(rand_indexes) == 1:
                rank = self._get_rank_of_image(image, self._images.CLASSES[rand_indexes[0]])

                self._ranks['user']['uniform'].append(rank)
                self._ranks['user']['idf'].append(rank)
            elif len(rand_indexes) > 1:
                array = self._images.CLASSES[rand_indexes[0]] + self._images.CLASSES[rand_indexes[1]]
                i = 2
                while i < len(rand_indexes):
                    array += self._images.CLASSES[rand_indexes[i]]
                    i += 1
                rank = self._get_rank_of_image(image, array)

                self._ranks['user']['uniform'].append(rank)

                array = self._idf.IDF[rand_indexes[0]] * self._images.CLASSES[rand_indexes[0]] + \
                    self._idf.IDF[rand_indexes[1]] * self._images.CLASSES[rand_indexes[1]]
                i = 2
                while i < len(rand_indexes):
                    array += self._idf.IDF[rand_indexes[i]] * self._images.CLASSES[rand_indexes[i]]
                    i += 1
                rank = self._get_rank_of_image(image, array)

                self._ranks['user']['idf'].append(rank)

            pt.increment()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # common
    parser.add_argument('-i', type=str, default=None)
    parser.add_argument('-u', type=str, default=None)
    parser.add_argument('-g', type=str, default=None)
    parser.add_argument('--save', type=str, default=None)
    # perfect
    parser.add_argument('--perfect_user', action='store_true', default=False)
    parser.add_argument('--sample_size', type=int, default=None)
    parser.add_argument('--query_lengths', type=str, default=None)
    parser.add_argument('--restore_ranks', type=str, default=None)
    parser.add_argument('--restore_samples', type=str, default=None)
    # human
    parser.add_argument('--human_user', action='store_true', default=False)
    parser.add_argument('--label_file', type=str, default=None)
    parser.add_argument('--log_file', type=str, default=None)
    parser.add_argument('--hist', type=str, default=None)
    args = parser.parse_args()

    # read_queries
    #   'C:\\Users\\Tom\\Documents\\Visual Studio 2017\\Projects\\KeywordSelector\\' +
    #   'KeywordSelector\\bin\\Debug\\Log\\KeywordSelector_2017-12-04_14-35-45.txt'
    # read_labels
    #   'C:\\Users\\Tom\\Workspace\\ViretTool\\TestData\\TRECVid\\TRECVid-GoogLeNet.label'

    if args.human_user:
        h = HumanUserSimulation()
        if args.i is not None:
            h.read_images(args.i)
        if args.u is not None:
            h.read_mean(args.u)

        if args.label_file is not None and args.log_file is not None:
            h.parse_queries(args.log_file, args.label_file)
            #h.invert_index()
            #h.rank()

        if args.save is not None:
            h.save(args.save)

        if args.g is not None:
            h.graph(args.g)

        if args.hist is not None:
            h.histogram_of_hits(args.hist)

    if args.perfect_user and False:
        u = PerfectUserSimulation()
        if args.i is not None:
            u.read_images(args.i)
        if args.u is not None:
            u.read_mean(args.u)

        if args.restore_samples is not None:
            u.restore_samples(args.restore_samples)
        elif args.sample_size is not None:
            u.gen_samples(args.sample_size)

        if args.restore_ranks is not None:
            u.restore_ranks(args.restore_ranks)

        if args.query_lengths is not None:
            u.invert_index()
            u.rank([int(i) for i in args.query_lengths.split(',')])

        if args.save is not None:
            u.save(args.save)

        if args.g is not None:
            u.graph(args.g)


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