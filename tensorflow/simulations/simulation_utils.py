import struct
import random
import numpy as np


class Label:
    ID = None
    SYNSET_ID = None
    NAMES = None
    HYPONYMS = None
    HYPERNYMS = None
    DESCRIPTION = None


def read_labels(filename):
    labels = dict()

    with open(filename, 'r') as f:
        for line in f:
            parts = line.split('~')
            if len(parts) != 6:
                raise Exception()

            l = Label()
            l.SYNSET_ID = input(parts[1])
            l.NAMES = parts[2].split('#')
            if parts[0] != "H":
                l.ID = int(parts[0])
            l.HYPONYMS = [int(i) for i in parts[3].split('#')]
            l.HYPERNYMS = [int(i) for i in parts[4].split('#')]
            l.DESCRIPTION = parts[5]

            labels[l.SYNSET_ID] = l
    return labels


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
    IMAGES = None
    _CLASS_INDEXES = dict()

    def get_rank(self, image, class_index):
        if class_index in self._CLASS_INDEXES:
            l = self._CLASS_INDEXES[class_index]
        else:
            l = [i.get_ith(class_index) for _, i in self.items()]
            l.sort(key=lambda t: -t[1])
            self._CLASS_INDEXES[class_index] = l
        for (i, (img_id, _)) in enumerate(l):
            if img_id == image.ID:
                return i
        return None

    def items(self):
        return self.IMAGES.items()

    def __getitem__(self, key):
        return self.IMAGES[key]

    def read_images(self, filename):
        self.IMAGES = dict()
        dt = np.dtype(np.float32).newbyteorder('<')

        with open(filename, 'rb') as f:
            dimension = struct.unpack('<I', f.read(4))[0]
            id_no = f.read(4)

            while id_no != b'':
                i = Image()
                i.ID = struct.unpack('<I', id_no)[0]
                i.DISTRIBUTION = np.frombuffer(f.read(dimension * 4), dtype=dt)

                self.IMAGES[i.ID] = i
                id_no = f.read(4)


class IDF:
    TERM_COUNT = None
    IDF = None

    def read_term_count(self, filename):
        dt = np.dtype(np.float32).newbyteorder('<')

        with open(filename, 'rb') as f:
            dimension = struct.unpack('<I', f.read(4))[0]
            self.TERM_COUNT = np.frombuffer(f.read(dimension * 4), dtype=dt)

    def compute_idf(self):
        self.IDF = np.log(np.sum(self.TERM_COUNT) / (self.TERM_COUNT + 1))

    def print(self):
        for i in range(len(self.TERM_COUNT)):
            print(str(self.TERM_COUNT[i]) + " -> " + str(self.IDF[i]))
