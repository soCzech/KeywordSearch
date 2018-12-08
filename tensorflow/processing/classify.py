import argparse
import os
import struct
import numpy as np
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
import tensorflow as tf

from models import network
from common_utils import console, dataset, input_pipeline
from common_utils.dataset import DEFAULT_HEADER
HEADER = DEFAULT_HEADER


def run(filenames, num_classes, model_path, run_name, prob_threshold=0.001, calc_cov=True):
    """Classifies given images and creates deep-feature and softmax output raw files.

    Args:
        filenames: Images to classify.
        num_classes: Number of classes in the last layer.
        model_path: Path to the checkpoint file of the neural network weights.
        run_name: Path and name of the output files.
        prob_threshold: Threshold :math:`\\mu`. Labels with probability smaller than :math:`\\mu` will not be saved.
        calc_cov: Calculate :math:`\\mathbb{E}\\left[XY\\right]` and :math:`\\mathbb{E}\\left[X\\right]`
            needed for covariance matrix.
    """
    pt = console.ProgressTracker()
    pt.info(">> Initializing TensorFlow model...")

    keys, images = input_pipeline.make_batch_from_jpeg(filenames)

    session = tf.Session()
    session.run(tf.local_variables_initializer())

    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(sess=session, coord=coord)

    """
        Network model
    """
    use_inception = False
    use_large = True

    if use_inception:
        logits, net = network.build_net(images, num_classes, is_training=False)
        deep_features = tf.squeeze(net["AvgPool_0a_7x7"], [1, 2], name="DeepFeatures")
    else:
        logits, net = network.build_nasnet(images, num_classes, is_training=False, use_large=use_large)
        print(net)
        deep_features = net["DeepFeatures"]

    df_shape = deep_features.get_shape()[1]

    probabilities = tf.nn.softmax(logits, name="Probability")

    inception_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='InceptionV1')
    logit_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='Logits')

    """
        Covariance
    """
    if calc_cov:
        cum_X = tf.get_variable("Cumulative_X", shape=[num_classes], dtype=tf.float32,
                                initializer=tf.zeros_initializer)
        cum_XY = tf.get_variable("Cumulative_XY", shape=[num_classes, num_classes], dtype=tf.float32,
                                 initializer=tf.zeros_initializer)

        add_cum_X = tf.add(cum_X, tf.reduce_sum(probabilities, 0), name="UpdateAdd_X")
        add_cum_XY = tf.add(cum_XY, tf.matmul(tf.transpose(probabilities), probabilities), name="UpdateAdd_XY")

    session.run(tf.global_variables_initializer())

    if use_inception:
        saver = tf.train.Saver(var_list=inception_vars + logit_vars)
    else:
        saver = tf.train.Saver()
    saver.restore(session, model_path)

    annot_f = dataset.create_file(
        run_name + '.annotation',
        [('<I', num_classes)],
        HEADER
    )
    dpfea_f = dataset.create_file(
        run_name + '.deep-features',
        [('<I', df_shape)],
        HEADER
    )
    softm_f = dataset.create_file(
        run_name + '.softmax',
        [('<I', num_classes)],
        HEADER
    )

    pt.info(">> Classifying...")
    pt.reset(len(filenames))

    try:
        while not coord.should_stop():
            if calc_cov:
                r_keys, r_cum_X, r_cum_XY, r_prob, r_dp_ftr = session.run([
                    keys, add_cum_X, add_cum_XY, probabilities, deep_features
                ])
            else:
                r_keys, r_prob, r_dp_ftr = session.run([keys, probabilities, deep_features])

            for i in range(len(r_keys)):
                _, filename = os.path.split(r_keys[i])

                if isinstance(filenames, dict):
                    file_id = filenames[r_keys[i].decode("utf-8")]
                else:
                    file_id = int(filename[:-4])

                r_top_indexes = np.where(r_prob[i] >= prob_threshold)[0]
                m_len = len(r_top_indexes)
                r_top_vals = np.zeros(m_len)

                for b in range(m_len):
                    r_top_vals[b] = r_prob[i][r_top_indexes[b]]

                annot_f.write(struct.pack('<I', file_id))

                annot_f.write(struct.pack('<I', m_len))
                annot_f.write(struct.pack('<' + 'I' * m_len, *r_top_indexes) +
                              struct.pack('<' + 'f' * m_len, *r_top_vals))

                dpfea_f.write(struct.pack('<I', file_id))
                dpfea_f.write(struct.pack('<' + 'f' * df_shape, *r_dp_ftr[i]))

                softm_f.write(struct.pack('<I', file_id))
                softm_f.write(struct.pack('<' + 'f' * num_classes, *r_prob[i]))

            pt.increment(len(r_keys))
    except tf.errors.OutOfRangeError:
        pt.info(">> Classification completed.")
    finally:
        if calc_cov:
            frmt = '<' + 'f' * len(r_cum_X)

            # save sum of X
            cum_X_f = dataset.create_file(run_name + '.sumX', [('<I', len(r_cum_X))], HEADER)
            cum_X_f.write(struct.pack(frmt, *r_cum_X))
            cum_X_f.close()

            # save sum of XY
            cum_XY_f = dataset.create_file(run_name + '.sumXY', [('<I', len(r_cum_XY))], HEADER)
            for i in range(len(r_cum_XY)):
                cum_XY_f.write(struct.pack(frmt, *r_cum_XY[i]))
            cum_XY_f.close()

        annot_f.close()
        dpfea_f.close()
        softm_f.close()

        # When done, ask the threads to stop.
        coord.request_stop()

        # Wait for threads to finish.
        coord.join(threads)
        session.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--image_dir', required=True, help='directory where to find images for classification')
    parser.add_argument('--num_classes', type=int, required=True)
    parser.add_argument('--model_path', required=True)
    parser.add_argument('--run_name', required=True)
    parser.add_argument('--prob_threshold', type=float, default=0.001)
    parser.add_argument('--calc_cov', action='store_true', default=False)
    args = parser.parse_args()

    images = dataset.get_images_from_disk(args.image_dir)

    run(images, args.num_classes, model_path=args.model_path, run_name=args.run_name,
        prob_threshold=args.prob_threshold, calc_cov=args.calc_cov)
