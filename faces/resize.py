import os
import glob
from PIL import Image


WIDTH = 1280
HEIGHT = 720


def get_images(folder):
    files = []
    for ext in ["*.jpg", "*.jpeg", "*.png"]:
        files.extend(glob.glob(os.path.join(folder, ext)))
    return files


def resize(images, output_dir):
    for i, im in enumerate(images):
        print("\r{:7d}/{:7d}".format(i + 1, len(images)), end="")
        basename = ".".join(os.path.basename(im).split(".")[:-1])

        im = Image.open(im)
        im = im.convert('RGB')

        if im.width != WIDTH or im.height != HEIGHT:
            im = im.resize((WIDTH, HEIGHT), Image.BILINEAR)

        im.save(os.path.join(output_dir, basename + ".jpg"))


imgs = get_images("test")
resize(imgs, "jpg")
