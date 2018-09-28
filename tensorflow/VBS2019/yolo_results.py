import os
import cv2
import json
import numpy as np
from matplotlib import pyplot as plt

import random
import colorsys


class Image:

    def __init__(self, filename):
        self.filename = filename
        image = cv2.imread(filename)
        self.image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.text_dx = 0
        self.text_dy = -10

    def save(self, filename=None, suffix=None, folder=None):
        new = self.filename
        if filename is not None:
            new = filename
        if folder is not None:
            folder = os.path.normpath(os.path.join(os.path.dirname(new), folder))
            if not os.path.exists(folder):
                os.makedirs(folder)
            new = os.path.join(folder, os.path.basename(new))
        if suffix is not None:
            new = "".join(new.split(".")[:-1]) + suffix + "." + new.split(".")[-1]
        cv2.imwrite(new, self.image)

    def display(self):
        plt.figure(dpi=100)
        plt.imshow(self.image)
        plt.axis('off')
        plt.show()

    def draw_rectangles(self, rectangles, text):
        for rect, label in zip(rectangles, text):
            p1 = (int(rect[0] - rect[2]/2), int(rect[1] - rect[3]/2))
            p2 = (int(rect[0] + rect[2]/2), int(rect[1] + rect[3]/2))

            color = Image.random_color()
            cv2.rectangle(self.image, p1, p2, color, 3, 4)
            cv2.putText(self.image, label, (p1[0] + self.text_dx, p1[1] + self.text_dy), cv2.FONT_HERSHEY_SIMPLEX, .6, color, 2)

    def put_text(self, texts):
        color = Image.random_color()
        for i, label in enumerate(texts):
            cv2.putText(self.image, label, (int(self.image.shape[1] * 1 / 3 + 10), int(self.image.shape[0] - (len(texts) - i) * 30)),
                        cv2.FONT_HERSHEY_SIMPLEX, .6, color, 2)

    def draw_relative_rectangles(self, rectangles, text):
        iw = self.image.shape[1]
        ih = self.image.shape[0]
        # print(iw, ih)
        rectangles = [[x*iw, y*ih, w*iw, h*ih] for x, y, w, h in rectangles]
        return self.draw_rectangles(rectangles, text)

    @staticmethod
    def random_color():
        h, s, l = random.random(), 0.5 + random.random() / 2.0, 0.4 + random.random() / 5.0
        return tuple([int(256 * i) for i in colorsys.hls_to_rgb(h, l, s)])


def json2img(json_file):
    with open(json_file, "r") as f:
        content = json.loads(f.read())

    for key in content.keys():
        img = Image(key.replace("/mnt/c", "c:"))

        rect = [i[2] for i in content[key]]
        text = ["{} {:.1f}%".format(i[0], i[1]*100) for i in content[key]]
        img.draw_rectangles(rect, text)
        img.save(suffix="_edited", folder="../random_00100_yolo9000")


if __name__ == "__main__":
    json2img("external/yolo_results.json")
