import os
import struct
import shutil
import numpy as np

from common_utils import console, dataset
from common_utils.dataset import DEFAULT_HEADER
HEADER = DEFAULT_HEADER


class KeywordVector:
    """
    A wrapper for an distribution vector.
    """
    ID = None
    DISTRIBUTION = None

    def get_ith(self, index):
        return self.ID, self.DISTRIBUTION[index]


class Keywords:
    """
    A class holding label distributions.
    """

    def __init__(self):
        self.NO_CLASSES = 0
        self.NO_IMAGES = 0
        self.CLASSES = dict()

    def __getitem__(self, key):
        """
        Returns:
            KeywordVector object for given image id.
        """
        kv = KeywordVector()
        kv.ID = key
        kv.DISTRIBUTION = np.zeros(self.NO_CLASSES, dtype=np.dtype(np.float32))
        for i in range(self.NO_CLASSES):
            kv.DISTRIBUTION[i] = self.CLASSES[i][key]
        kv.DISTRIBUTION /= np.sum(kv.DISTRIBUTION)
        return kv

    def __len__(self):
        return self.NO_IMAGES

    def read_images(self, filename):
        """
        Reads index of image mappings [images, classes] from a file.
        """
        if os.path.isfile(filename + ".inverted"):
            self._read_inverted_index(filename + ".inverted")
            return

        images = dict()
        dt = np.dtype(np.float32).newbyteorder("<")

        with dataset.read_file(filename, HEADER) as f:
            self.NO_CLASSES = struct.unpack("<I", f.read(4))[0]
            id_no = f.read(4)

            pt = console.ProgressTracker()
            pt.info(">> Reading image vectors...")

            self.NO_IMAGES = 0
            while id_no != b'':
                kv = KeywordVector()
                kv.ID = struct.unpack("<I", id_no)[0]
                kv.DISTRIBUTION = np.frombuffer(f.read(self.NO_CLASSES * 4), dtype=dt)
                self.NO_IMAGES += 1

                images[kv.ID] = kv
                id_no = f.read(4)

        self._invert_index(filename + ".inverted", images)

    def _invert_index(self, filename, images):
        """
        Inverts index from [images, classes] to [classes, images] for faster access.

        Args:
            filename: location where to store the inverted index.
            images: numpy array of [images, classes]
        """
        pt = console.ProgressTracker()

        if not os.path.isfile(filename):
            pt.info(">> Inverting image vectors...")
            pt.reset(self.NO_CLASSES)

            for i in range(self.NO_CLASSES):
                self.CLASSES[i] = np.zeros(len(images))
                for image in images.values():
                    self.CLASSES[i][image.ID] = image.DISTRIBUTION[i]
                pt.increment()
            pt.info(">> Saving inverted vectors...")
            pt.reset(self.NO_CLASSES)

            with dataset.create_file(filename, [("<I", len(self.CLASSES)), ("<I", len(self.CLASSES[0]))], HEADER) as f:
                for i in range(self.NO_CLASSES):
                    f.write(struct.pack("<" + "f" * len(self.CLASSES[i]), *self.CLASSES[i]))
                    pt.increment()

    def _read_inverted_index(self, filename):
        """
        Reads inverted index and stores it into `self.CLASSES`.
        """
        pt = console.ProgressTracker()

        with dataset.read_file(filename, HEADER) as f:
            pt.info(">> Reading inverted vectors...")
            self.NO_CLASSES = struct.unpack("<I", f.read(4))[0]

            pt.reset(self.NO_CLASSES)
            self.NO_IMAGES = struct.unpack("<I", f.read(4))[0]

            dt = np.dtype(np.float32).newbyteorder("<")
            for i in range(self.NO_CLASSES):
                self.CLASSES[i] = np.frombuffer(f.read(self.NO_IMAGES * 4), dtype=dt)
                self.CLASSES[i].setflags(write=1)
                pt.increment()


class IDF:
    """
    A class to load and hold IDF for the dataset.
    """

    def __init__(self):
        self.TERM_COUNT = None
        self.IDF = None

    def read_term_count(self, filename):
        """
        Loads term count from file.

        Args:
            filename: a file to load from.
        """
        dt = np.dtype(np.float32).newbyteorder('<')

        with dataset.read_file(filename, HEADER) as f:
            dimension = struct.unpack('<I', f.read(4))[0]
            self.TERM_COUNT = np.frombuffer(f.read(dimension * 4), dtype=dt)

    def compute_idf(self):
        """
        Compute IDF as :math:`\\log\\left(\\frac{\\max_c c}{c} +1\\right)` where :math:`c` is a an image class.
        """
        self.IDF = np.log(np.amax(self.TERM_COUNT) / (self.TERM_COUNT + 0.00001) + 1)

    def print_idf(self):
        """
        Prints IDF for all classes.
        """
        for i in range(len(self.TERM_COUNT)):
            print(str(self.TERM_COUNT[i]) + " -> " + str(self.IDF[i]))


def __copy_image_files_to_one_dir(from_dir, to_dir):
    """
    Copies files from video directories to one directory and renames them.
    """
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
