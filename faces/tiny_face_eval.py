# -*- coding: utf-8 -*-
import os
# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import tensorflow as tf
import tiny_face_model
import argparse
import numpy as np
import cv2

import pylab as pl
from scipy.special import expit
import glob


MAX_INPUT_DIM = 5000.0


def overlay_bounding_boxes(raw_img, refined_bboxes):
    color = [252, 244, 32]

    for bbox in refined_bboxes:
        score = expit(bbox[4])
        p1 = (int(bbox[0]), int(bbox[1]))
        p2 = (int(bbox[2]), int(bbox[3]))

        cv2.rectangle(raw_img, p1, p2, color, 2)
        cv2.putText(raw_img, "{:.1f}%".format(score * 100), (p1[0], p1[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, .6, color, 1)


def get_images(folder):
    return glob.glob(os.path.join(folder, "*.jpg"))


def calc_scales(raw_img=None, clusters=None):
    if raw_img is None or clusters is None:
        return [0.0625, 0.125, 0.25, 0.5, 1., 1.4142, 2.]

    clusters_h = clusters[:, 3] - clusters[:, 1] + 1
    clusters_w = clusters[:, 2] - clusters[:, 0] + 1
    normal_idx = np.where(clusters[:, 4] == 1)

    raw_h, raw_w = raw_img.shape[0], raw_img.shape[1]
    min_scale = min(np.floor(np.log2(np.max(clusters_w[normal_idx] / raw_w))),
                    np.floor(np.log2(np.max(clusters_h[normal_idx] / raw_h))))
    max_scale = min(1.0, -np.log2(max(raw_h, raw_w) / MAX_INPUT_DIM))
    scales_down = pl.frange(min_scale, 0, 1.)
    scales_up = pl.frange(0.5, max_scale, 0.5)
    scales_pow = np.hstack((scales_down, scales_up))
    scales = np.power(2.0, scales_pow)
    return scales[:-2]


def calc_bounding_boxes(score_final_tf, clusters, scale, prob_thresh=0.25):
    # we don't run every template on every scale ids of templates to ignore
    tids = list(range(4, 12)) + ([] if scale <= 1.0 else list(range(18, 25)))
    ignoredTids = list(set(range(0, clusters.shape[0])) - set(tids))

    # collect scores
    score_cls_tf, score_reg_tf = score_final_tf[:, :, :, :25], score_final_tf[:, :, :, 25:125]
    prob_cls_tf = expit(score_cls_tf)
    prob_cls_tf[0, :, :, ignoredTids] = 0.0

    # threshold for detection
    _, fy, fx, fc = np.where(prob_cls_tf > prob_thresh)

    # interpret heatmap into bounding boxes
    cy = fy * 8 - 1
    cx = fx * 8 - 1
    ch = clusters[fc, 3] - clusters[fc, 1] + 1
    cw = clusters[fc, 2] - clusters[fc, 0] + 1

    # extract bounding box refinement
    Nt = clusters.shape[0]
    tx = score_reg_tf[0, :, :, 0:Nt]
    ty = score_reg_tf[0, :, :, Nt:2 * Nt]
    tw = score_reg_tf[0, :, :, 2 * Nt:3 * Nt]
    th = score_reg_tf[0, :, :, 3 * Nt:4 * Nt]

    # refine bounding boxes
    dcx = cw * tx[fy, fx, fc]
    dcy = ch * ty[fy, fx, fc]
    rcx = cx + dcx
    rcy = cy + dcy
    rcw = cw * np.exp(tw[fy, fx, fc])
    rch = ch * np.exp(th[fy, fx, fc])

    scores = score_cls_tf[0, fy, fx, fc]
    tmp_bboxes = np.vstack((rcx - rcw / 2, rcy - rch / 2, rcx + rcw / 2, rcy + rch / 2))
    tmp_bboxes = np.vstack((tmp_bboxes / scale, scores))
    tmp_bboxes = tmp_bboxes.transpose()
    return tmp_bboxes


def create_batch(images, average_image, scale):
    batch = []
    for img in images:
        img = cv2.resize(img, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
        img = img - average_image
        img = np.expand_dims(img, axis=0)
        batch.append(img)

    batch = np.vstack(batch)
    return batch


def read_file(filename):
    raw_img = cv2.imread(filename)
    raw_img = cv2.cvtColor(raw_img, cv2.COLOR_BGR2RGB)
    raw_img_f = raw_img.astype(np.float32)
    return raw_img, raw_img_f


def get_refined_boxes(bboxes, sess):
    refined_idx = tf.image.non_max_suppression(tf.convert_to_tensor(bboxes[:, :4], dtype=tf.float32),
                                               tf.convert_to_tensor(bboxes[:, 4], dtype=tf.float32),
                                               max_output_size=bboxes.shape[0], iou_threshold=0.1)
    refined_idx = sess.run(refined_idx)
    return bboxes[refined_idx]


def evaluate(weight_file_path, data_dir, output_dir):
    # placeholder of input images. Currently batch size of one is supported.
    x = tf.placeholder(tf.float32, [1, None, None, 3]) # n, h, w, c

    # Create the tiny face model which weights are loaded from a pretrained model.
    model = tiny_face_model.Model(weight_file_path)
    score_final = model.tiny_face(x)

    average_image = model.get_weights("average_image")
    clusters = model.get_weights("clusters")

    # main
    sess = tf.Session()
    sess.run(tf.global_variables_initializer())

    for filename in get_images(data_dir):
        fname = filename.split(os.sep)[-1]
        raw_img, raw_img_f = read_file(filename)

        scales = calc_scales(raw_img, clusters)

        # initialize output
        bboxes = np.empty(shape=(0, 5))

        # process input at different scales
        for s in scales:
            batch = create_batch([raw_img_f], average_image, s)
            # run through the net
            score_final_tf = sess.run(score_final, feed_dict={x: batch})

            tmp_bboxes = calc_bounding_boxes(score_final_tf, clusters, s)
            bboxes = np.vstack((bboxes, tmp_bboxes)) # <class 'tuple'>: (5265, 5)

        refined_bboxes = get_refined_boxes(bboxes, sess)
        overlay_bounding_boxes(raw_img, refined_bboxes)

        # save image with bounding boxes
        raw_img = cv2.cvtColor(raw_img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(os.path.join(output_dir, fname), raw_img)


if __name__ == '__main__':
    argparse = argparse.ArgumentParser()
    argparse.add_argument('--weight_file_path', type=str, help='Pretrained weight file.', default="hr_res101.pickle")
    argparse.add_argument('--data_dir', type=str, help='Image data directory.', default="jpg")
    argparse.add_argument('--output_dir', type=str, help='Output directory for images with faces.', default="output")
    args = argparse.parse_args()

    evaluate(weight_file_path=args.weight_file_path, data_dir=args.data_dir, output_dir=args.output_dir)
