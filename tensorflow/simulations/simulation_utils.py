import os
import struct
import random
import numpy as np
from common_utils import console


class Label:
    ID = None
    SYNSET_ID = None
    NAMES = None
    HYPONYMS = []
    HYPERNYMS = []
    DESCRIPTION = None

    @staticmethod
    def read_labels(filename):
        labels = dict()

        with open(filename, 'r') as f:
            for line in f:
                parts = line.split('~')
                if len(parts) != 6:
                    raise Exception()

                l = Label()
                l.SYNSET_ID = int(parts[1])
                l.NAMES = parts[2].split('#')
                if parts[0] != "H":
                    l.ID = int(parts[0])
                if parts[3] != "":
                    l.HYPONYMS = [int(i) for i in parts[3].split('#')]
                if parts[4] != "":
                    l.HYPERNYMS = [int(i) for i in parts[4].split('#')]
                l.DESCRIPTION = parts[5]

                labels[l.SYNSET_ID] = l
        return labels

    @staticmethod
    def expand_query(labels, query):

        def expand_hyponyms(hyponyms):
            l = []
            for h in hyponyms:
                if labels[h].ID is not None:
                    l.append(labels[h].ID)
                l.extend(expand_hyponyms(labels[h].HYPONYMS))
            return l

        l = []
        for synset_id, use_children in query:
            if use_children:
                if labels[synset_id].ID is not None:
                    l.append(labels[synset_id].ID)
                l.extend(expand_hyponyms(labels[synset_id].HYPONYMS))
            else:
                l.append(labels[synset_id].ID)
        return list(set(l))


def get_random_index_from_dist(dist):
    rnd = random.random()
    s = 0
    index = 0

    while s <= rnd and index < len(dist):
        s += dist[index]
        index += 1

    return index - 1


class Image:
    ID = None
    DISTRIBUTION = None

    def get_ith(self, index):
        return self.ID, self.DISTRIBUTION[index]


class Images:
    DIMENSION = 0
    IMAGES = dict()
    CLASSES = dict()

    def get_rank(self, image, class_index):
        l = [i.get_ith(class_index) for i in self.IMAGES.values()]
        l.sort(key=lambda t: -t[1])

        for (i, (img_id, _)) in enumerate(l):
            if img_id == image.ID:
                return i
        return None

    def __getitem__(self, key):
        return self.IMAGES[key]

    def read_images(self, filename):
        pt = console.ProgressTracker()
        pt.info(">> Reading image vectors...")

        self.IMAGES = dict()
        dt = np.dtype(np.float32).newbyteorder('<')

        with open(filename, 'rb') as f:
            self.DIMENSION = struct.unpack('<I', f.read(4))[0]
            id_no = f.read(4)

            while id_no != b'':
                i = Image()
                i.ID = struct.unpack('<I', id_no)[0]
                i.DISTRIBUTION = np.frombuffer(f.read(self.DIMENSION * 4), dtype=dt)

                self.IMAGES[i.ID] = i
                id_no = f.read(4)

    def invert_index(self, filename):
        pt = console.ProgressTracker()

        if not os.path.isfile(filename):
            pt.info(">> Inverting image vectors...")
            pt.reset(self.DIMENSION)

            for i in range(self.DIMENSION):
                self.CLASSES[i] = np.zeros(len(self.IMAGES))
                for image in self.IMAGES.values():
                    self.CLASSES[i][image.ID] = image.DISTRIBUTION[i]
                pt.increment()
            pt.info(">> Saving inverted vectors...")
            pt.reset(self.DIMENSION)

            with open(filename, 'wb') as f:
                f.write(struct.pack('<I', len(self.CLASSES)))
                f.write(struct.pack('<I', len(self.CLASSES[0])))
                for i in range(self.DIMENSION):
                    f.write(struct.pack('<' + 'f' * len(self.CLASSES[i]), *self.CLASSES[i]))
                    pt.increment()
        else:
            with open(filename, 'rb') as f:
                pt.info(">> Reading inverted vectors...")
                pt.reset(self.DIMENSION)

                assert self.DIMENSION == struct.unpack('<I', f.read(4))[0]
                assert len(self.IMAGES) == struct.unpack('<I', f.read(4))[0]

                dt = np.dtype(np.float32).newbyteorder('<')
                for i in range(self.DIMENSION):
                    self.CLASSES[i] = np.frombuffer(f.read(len(self.IMAGES) * 4), dtype=dt)
                    self.CLASSES[i].setflags(write=1)
                    pt.increment()


class IDF:
    TERM_COUNT = None
    IDF = None

    def read_term_count(self, filename):
        dt = np.dtype(np.float32).newbyteorder('<')

        with open(filename, 'rb') as f:
            dimension = struct.unpack('<I', f.read(4))[0]
            self.TERM_COUNT = np.frombuffer(f.read(dimension * 4), dtype=dt)

    def compute_idf(self):
        self.IDF = np.log2(np.amax(self.TERM_COUNT)*2 / self.TERM_COUNT)

    def print(self):
        for i in range(len(self.TERM_COUNT)):
            print(str(self.TERM_COUNT[i]) + " -> " + str(self.IDF[i]))


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
        return np.dot(x, y) / (np.sqrt(np.dot(x, x)) * np.sqrt(np.dot(y, y)))

    @staticmethod
    def l2_dist(x, y):
        dxy = x - y
        return np.sqrt(np.dot(dxy, dxy))

    def get_distance_vector(self, query_image_index):
        rank = np.zeros(len(self.VECTORS))

        for i in range(len(self.VECTORS)):
            rank[i] = self.cos_dist(self.VECTORS[query_image_index].astype(np.float32), self.VECTORS[i].astype(np.float32))
        return rank

    def get_rank_vector(self, query_image_index):
        return np.argsort(self.get_distance_vector(query_image_index))

    def get_rank(self, query_image_index, searched_image_index):
        if not isinstance(searched_image_index, list):
            searched_image_index = [searched_image_index]

        rank_vec = self.get_rank_vector(query_image_index)
        ret_list = []

        for index in searched_image_index:
            for i in range(len(rank_vec)):
                if rank_vec[i] == index:
                    ret_list.append(i)
                    break

        if len(ret_list) == 1:
            return ret_list[0]
        return ret_list

    def get_best_rank(self, query_image_indexes, searched_image_index):
        best_rank = None, 2147483647
        for index in query_image_indexes:
            dist = self.cos_dist(self.VECTORS[index].astype(np.float32), self.VECTORS[searched_image_index].astype(np.float32))
            if best_rank[1] > dist:
                best_rank = index, dist

        return self.get_rank(best_rank[0], searched_image_index)
