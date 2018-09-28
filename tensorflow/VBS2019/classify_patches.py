import os
import math
import numpy as np
import tensorflow as tf
from models import network, inception_preprocessing
from VBS2019.yolo_results import Image


num_classes = 1150


sess = tf.Session()
filename = tf.placeholder(tf.string)
image = tf.image.decode_png(filename, channels=3)


def read_img(fn):
    fn = tf.gfile.FastGFile(fn, 'rb').read()
    return sess.run(image, feed_dict={filename: fn})


raw_image = tf.placeholder(tf.uint8)
prep_image = inception_preprocessing.preprocess_image(raw_image, 224, 224, is_training=False, central_fraction=None)


def prep_img(ri):
    return sess.run(prep_image, feed_dict={raw_image: ri})


input_batch = tf.placeholder(tf.float32, shape=[None, 224, 224, 3])

logits, net = network.build_net(input_batch, num_classes, is_training=False)
probabilities = tf.nn.softmax(logits, name="Probability")

inception_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='InceptionV1')
logit_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='Logits')

sess.run(tf.global_variables_initializer())

saver = tf.train.Saver(var_list=inception_vars + logit_vars)
saver.restore(sess, "../data/training/checkpoints/inception_retrained-80-53.09.ckpt-140000")


def eval_batch(batch):
    return sess.run(probabilities, feed_dict={input_batch: batch})


def get_images(folder):
    folder = os.path.abspath(folder)
    return [os.path.join(folder, img) for img in os.listdir(folder)]


def load_labels(file):
    d = {}
    with open(file, "r") as f:
        for line in f:
            line = line.split("~")
            if line[0] == "H":
                continue
            d[int(line[0])] = ", ".join(line[2].split("#"))
    return d


labels = load_labels("../../ITEC-GoogLeNet.label")

for img_name in get_images("../../random_00100"):
    print(img_name)
    img = read_img(img_name)
    print("\t", img.shape, img.dtype)

    def chunks(array_len, n):
        chunk = int(math.ceil(array_len / n))
        current = 1
        while current < n:
            ret = chunk * current
            current += 1
            yield ret

    h_splits = np.split(img, indices_or_sections=list(chunks(img.shape[0], 2)), axis=0)
    all_splits = []
    for i, split in enumerate(h_splits):
        w_splits = np.split(split, indices_or_sections=list(chunks(img.shape[1], 3)), axis=1)

        for j, split in enumerate(w_splits):
            all_splits.append((i, j, split))

    middle_row = np.split(img, indices_or_sections=[int(img.shape[0]/4), int(img.shape[0]*3/4)], axis=0)[1]
    print("\t", middle_row.shape)
    center_boxes = np.split(middle_row, indices_or_sections=[int(img.shape[1]/6), int(img.shape[1]/2), int(img.shape[1]*5/6)], axis=1)
    all_splits.extend([(1/2, 1/2, center_boxes[1]), (1/2, 3/2, center_boxes[2])])

    print("\t", [(i, j, s.shape) for i, j, s in all_splits])

    preps = [(i, j, prep_img(s).reshape([1, 224, 224, 3])) for i, j, s in all_splits]
    print("\t", [(s.shape, s.dtype) for i, j, s in preps])

    batch = np.concatenate([s for _, _, s in preps] + [prep_img(img).reshape([1, 224, 224, 3])], axis=0)
    print("\t", batch.shape, batch.dtype)

    res = eval_batch(batch)
    print("\t", res.shape, res.dtype)

    top_cls = np.argsort(res, axis=1)
    text_res = [(labels[top_cls[i][-1]], res[i][top_cls[i][-1]]) for i in range(len(top_cls))]
    print("\t", text_res)

    cimg = Image(img_name)
    cimg.text_dy = 30
    cimg.text_dx = 10
    cimg.draw_relative_rectangles([[(j+1/2) * 1/3, (i+1/2) * 1/2, 1/3, 1/2] for i, j, _ in preps],
                                  ["{} {:.1f}%".format(cls[:30], prob*100) for cls, prob in text_res[:-1]])
    cimg.put_text(["{} {:.1f}%".format(cls[:30], prob*100) for cls, prob in [
        (labels[top_cls[-1][-i]], res[-1][top_cls[-1][-i]]) for i in range(1, 6)
    ]])
    cimg.save(suffix="_edited", folder="../6patches")
