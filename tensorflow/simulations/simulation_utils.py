import os
import struct
import random
import numpy as np
from common_utils import console
from PIL import Image as pImage, ImageDraw as pDraw, ImageFont as pFont
import shutil


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
        self.IDF = 1 + np.log2(np.amax(self.TERM_COUNT) / self.TERM_COUNT)

    def print(self):
        for i in range(len(self.TERM_COUNT)):
            print(str(self.TERM_COUNT[i]) + " -> " + str(self.IDF[i]))


class SimilarityVisualization(console.Singleton):
    MAX_IMAGES = None
    MAX_ITERATIONS = None
    IMAGE_DIMS = None
    IMAGE = None
    CANVAS = None
    CURRENT = None
    ITERATION = None
    IMAGE_DIR = None

    def initialize(self, max_images, max_iterations, image_dims, image_dir):
        self.MAX_IMAGES = max_images
        self.MAX_ITERATIONS = max_iterations
        self.IMAGE_DIMS = image_dims
        self.IMAGE = pImage.new('RGB', (image_dims[0] * max_iterations, image_dims[1] * max_images), (255, 255, 255))
        self.CANVAS = pDraw.Draw(self.IMAGE)
        self.CURRENT = -1
        self.ITERATION = -1
        self.IMAGE_DIR = image_dir

    def new_image(self, image_id):
        if self.CURRENT >= self.MAX_IMAGES:
            return

        self.CURRENT += 1
        self.ITERATION = 0
        self.new_iteration(image_id, text="ID " + str(image_id))

    def new_iteration(self, image_id, text=None):
        if self.ITERATION >= self.MAX_ITERATIONS:
            return

        x = self.ITERATION * self.IMAGE_DIMS[0]
        y = self.CURRENT * self.IMAGE_DIMS[1]

        img = pImage.open(os.path.join(self.IMAGE_DIR, str(image_id).zfill(7) + ".jpg"))
        img = img.resize((self.IMAGE_DIMS[0], self.IMAGE_DIMS[1]))
        self.IMAGE.paste(img, (x, y, x + self.IMAGE_DIMS[0], y + self.IMAGE_DIMS[1]))

        if text is not None:
            font = pFont.truetype("courbd", 18)
            if isinstance(text, list):
                self.CANVAS.text((x, y), text[0], fill=(0, 255, 0, 255), font=font)
                self.CANVAS.text((x, y + self.IMAGE_DIMS[1] - 18), text[1], fill=(0, 255, 0, 255), font=font)
            else:
                self.CANVAS.text((x, y), text, fill=(0, 255, 0, 255), font=font)
        self.ITERATION += 1

    def save(self, filename):
        self.IMAGE.save("C:\\Users\\Tom\\Workspace\\KeywordSearch\\image" + filename + ".jpg", "JPEG")


def copy_files(from_dir, to_dir):
    pt = console.ProgressTracker()

    if not os.path.exists(to_dir):
        os.mkdir(to_dir)

    dirs = os.listdir(from_dir)
    dirs.sort(key=int)

    pt.info(">> Copying files...")
    pt.reset(len(dirs))

    i = 0
    for d in dirs:
        directory = os.path.join(from_dir, d)
        for file in sorted(os.listdir(directory)):
            filename = os.path.join(directory, file)
            destination = os.path.join(to_dir, str(i).zfill(7) + ".jpg")
            shutil.copyfile(filename, destination)
            i += 1
        pt.increment()


#copy_files("E:\\VIRET\\Keyframes", "C:\\Users\\Tom\\Workspace\\KeywordSearch\\kw")
