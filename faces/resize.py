import os
import glob
from PIL import Image
from multiprocessing import Pool, Value
import itertools


WIDTH = 1280
HEIGHT = 720
SCALES = [(int(WIDTH * s), int(HEIGHT * s)) for s in [0.0625, 0.125, 0.25, 0.5, 1., 1.4142]]


def get_images(folder):
    files = []
    for ext in ["*.jpg", "*.jpeg", "*.png"]:
        files.extend(glob.glob(os.path.join(folder, "*", ext)))
    return files


def resize(images):
    output_dir = "_kf_resized"
    global counter

    for im in images:
        basename = ".".join(os.path.basename(im).split(".")[:-1])
        dir_name = im.split("/")[-2]
        if not os.path.exists(output_dir + "/" + dir_name):
            os.mkdir(output_dir + "/" + dir_name)

        im = Image.open(im)
        im = im.convert('RGB')

        for w, h in SCALES:
            im2 = im
            if im.width != w or im.height != h:
                im2 = im.resize((w, h), Image.BILINEAR)

            im2.save(os.path.join(output_dir, dir_name, basename + "_" + str(w) + "x" + str(h) + ".jpg"))

        with counter.get_lock():
            counter.value += 1
        print("\r{:7d}/{:7d}".format(counter.value, len(imgs)), end="")


def split_seq(iterable, size):
    it = iter(iterable)
    item = list(itertools.islice(it, size))
    while item:
        yield item
        item = list(itertools.islice(it, size))


counter = Value('i', 0)
imgs = get_images("_kf")


with Pool(32) as p:
    p.map(resize, split_seq(imgs, 1000))

