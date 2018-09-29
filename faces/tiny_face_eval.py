import os
# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import tensorflow as tf
import tiny_face_model
import argparse
import numpy as np
import cv2

import pylab as pl
from scipy.special import expit as sigmoid
import glob


WIDTH = 1280
HEIGHT = 720
MAX_INPUT_DIM = 5000.0


def overlay_bounding_boxes(raw_img, refined_bboxes):
    color = [252, 244, 32]

    for bbox in refined_bboxes:
        score = sigmoid(bbox[4])
        p1 = (int(bbox[0]), int(bbox[1]))
        p2 = (int(bbox[2]), int(bbox[3]))

        cv2.rectangle(raw_img, p1, p2, color, 2)
        cv2.putText(raw_img, "{:.1f}%".format(score * 100), (p1[0], p1[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, .6, color, 1)


def get_images(folder):
    return glob.glob(os.path.join(folder, "*.jpg"))


def calc_scales(img_shape=None, clusters=None):
    if img_shape is None or clusters is None:
        return [0.0625, 0.125, 0.25, 0.5, 1., 1.4142, 2.]

    clusters_h = clusters[:, 3] - clusters[:, 1] + 1
    clusters_w = clusters[:, 2] - clusters[:, 0] + 1
    normal_idx = np.where(clusters[:, 4] == 1)

    raw_h, raw_w = img_shape[:2]
    min_scale = min(np.floor(np.log2(np.max(clusters_w[normal_idx] / raw_w))),
                    np.floor(np.log2(np.max(clusters_h[normal_idx] / raw_h))))
    max_scale = min(1.0, -np.log2(max(raw_h, raw_w) / MAX_INPUT_DIM))
    scales_down = pl.frange(min_scale, 0, 1.)
    scales_up = pl.frange(0.5, max_scale, 0.5)
    scales_pow = np.hstack((scales_down, scales_up))
    scales = np.power(2.0, scales_pow)
    return scales[:-2]


def calc_bounding_boxes(score_final_tf, clusters, scale, prob_thresh=0.5):
    # we don't run every template on every scale ids of templates to ignore
    tids = list(range(4, 12)) + ([] if scale <= 1.0 else list(range(18, 25)))
    ignoredTids = list(set(range(0, clusters.shape[0])) - set(tids))

    # collect scores
    score_cls_tf, score_reg_tf = score_final_tf[:, :, :, :25], score_final_tf[:, :, :, 25:125]
    prob_cls_tf = sigmoid(score_cls_tf)
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
    refined = []
    for bbox in bboxes:
        refined_idx = tf.image.non_max_suppression(tf.convert_to_tensor(bbox[:, :4], dtype=tf.float32),
                                                   tf.convert_to_tensor(bbox[:, 4], dtype=tf.float32),
                                                   max_output_size=bbox.shape[0], iou_threshold=0.1)
        refined_idx = sess.run(refined_idx)
        refined.append(bbox[refined_idx])
    return refined


def batch_files(files, batch_size=1):
    l = []
    for img in files:
        l.append(img)
        if len(l) == batch_size:
            res = l
            l = []
            yield res
    if len(l) > 0:
        yield l


def bboxes_to_numpy(bboxes):
    bits = np.zeros([18, 32], dtype=np.uint8)

    for bbox in bboxes:
        p1 = (int(bbox[0] * 0.025), int(bbox[1] * 0.025))
        p2 = (int(bbox[2] * 0.025), int(bbox[3] * 0.025))

        for i in range(p1[0], p2[0] + 1):
            for j in range(p1[1], p2[1] + 1):
                bits[i][j] = 1
    return bits


def evaluate(weight_file_path, data_dir, output_dir, threshold=0.5, batch_size=1):
    x = tf.placeholder(tf.float32, [None, None, None, 3])
    model = tiny_face_model.Model(weight_file_path)
    score_final = model.tiny_face(x)

    average_image = model.get_weights("average_image")
    clusters = model.get_weights("clusters")
    scales = calc_scales((HEIGHT, WIDTH), clusters)

    # main
    sess = tf.Session()
    sess.run(tf.global_variables_initializer())

    for file_names in batch_files(get_images(data_dir), batch_size=batch_size):
        files = []
        for file_name in file_names:
            raw_img, raw_img_f = read_file(file_name)
            files.append({
                "name": os.path.basename(file_name),
                "img_f": raw_img_f,
                "img": raw_img,
                "bboxes": np.empty(shape=(0, 5))
            })

        # process input at different scales
        for s in scales:
            batch = create_batch([f["img_f"] for f in files], average_image, s)
            score_final_tf = sess.run(score_final, feed_dict={x: batch})

            for i, f in enumerate(files):
                fscore = np.expand_dims(score_final_tf[i], axis=0)
                tmp_bboxes = calc_bounding_boxes(fscore, clusters, s, prob_thresh=threshold)
                f["bboxes"] = np.vstack([f["bboxes"], tmp_bboxes])

        refined_bboxes = get_refined_boxes([f["bboxes"] for f in files], sess)

        for rbb, file in zip(refined_bboxes, files):
            overlay_bounding_boxes(file["img"], rbb)

            raw_img = cv2.cvtColor(file["img"], cv2.COLOR_RGB2BGR)
            cv2.imwrite(os.path.join(output_dir, file["name"]), raw_img)


if __name__ == '__main__':
    argparse = argparse.ArgumentParser()
    argparse.add_argument("--weight_file", type=str, help="pretrained weight file", default="hr_res101.pickle")
    argparse.add_argument("--input_dir", type=str, help="image data directory", default="jpg")
    argparse.add_argument("--output_dir", type=str, help="output directory for images with faces", default="output")
    argparse.add_argument("--threshold", type=float, help="probability threshold", default=0.5)
    argparse.add_argument("--batch_size", type=int, default=1)

    args = argparse.parse_args()

    evaluate(weight_file_path=args.weight_file, data_dir=args.input_dir, output_dir=args.output_dir,
             threshold=args.threshold, batch_size=args.batch_size)
