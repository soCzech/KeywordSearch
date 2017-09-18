import argparse
import os
import sys
import struct
import numpy as np
import tensorflow as tf
from diagnostics import heatmap_utils
from models import network, model_utils, inception_v1


def run(filenames, num_classes, take_top_n, bin_dir, restore_all, calc_cov=True):
    if calc_cov:
        mean = np.zeros(num_classes, dtype=np.float)
        cov = np.zeros((num_classes, num_classes), dtype=np.float)
    keys, images = network.get_image_as_batch(filenames, inception_v1.default_image_size)

    session = tf.Session()
    session.run(tf.local_variables_initializer())

    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(sess=session, coord=coord)

    """
        Network model
    """
    logits, _ = network.build_net(images, num_classes, scope='InceptionGeneralist', is_training=False)

    inception_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='InceptionV1')
    generalist_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='InceptionGeneralist')

    probabilities = tf.nn.softmax(logits, name='Probability')
    top_values, top_indices = tf.nn.top_k(probabilities, k=take_top_n, sorted=True)

    """ Covariance """
    if calc_cov:
        probabilities = tf.nn.softmax(logits)

        last_mean = tf.placeholder(tf.float32, shape=num_classes)
        last_cov = tf.placeholder(tf.float32, shape=(num_classes, num_classes))

        add_to_mean = tf.add(last_mean, tf.reduce_sum(probabilities, 0))
        add_to_cov = tf.add(last_cov, tf.matmul(tf.transpose(probabilities), probabilities))
    """ END / Covariance """

    session.run(tf.global_variables_initializer())

    if restore_all:
        model_utils.restore_model(session, bin_dir, None)
    else:
        model_utils.restore_model(session, bin_dir, inception_vars, generalist_vars)

    pi_filename = os.path.join(os.path.normpath(bin_dir), 'files.pseudo-index')
    if os.path.isfile(pi_filename):
        raise Exception(pi_filename + ' exists.')
    file = open(pi_filename, 'wb')

    indices_format = '<' + 'I' * take_top_n
    values_format = '<' + 'f' * take_top_n

    i = 0
    try:
        while not coord.should_stop():
            if calc_cov:
                r_keys, r_top_v, r_top_i, mean, cov = session.run([
                    keys, top_values, top_indices, add_to_mean, add_to_cov
                ], feed_dict={last_mean: mean, last_cov: cov})
            else:
                r_keys, r_top_v, r_top_i = session.run([keys, top_values, top_indices])

            for a in range(len(r_keys)):
                _, filename = os.path.split(r_keys[a])
                file_id = int(filename[:-4])

                data = struct.pack(indices_format, *r_top_i[a]) + struct.pack(values_format, *r_top_v[a])

                file.write(struct.pack('<I', file_id))
                file.write(data)

            i += len(r_keys)
            sys.stdout.write('\r>> Classifying... {} ({:d}/{:d})'.format(filename, i, len(filenames)))
            sys.stdout.flush()
    except tf.errors.OutOfRangeError:
        sys.stdout.write('\r>> Classification completed.\n')
        sys.stdout.flush()
    finally:
        if calc_cov:
            heatmap_utils.store_covariance_matrix(
                mean, cov, len(filenames), os.path.join(bin_dir, 'covariance'), 'classification'
            )
        file.close()

        # When done, ask the threads to stop.
        coord.request_stop()

        # Wait for threads to finish.
        coord.join(threads)
        session.close()


# py actions/classify.py --image_dir=../_test/classification --num_classes=2
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--image_dir', required=True,
                        help='directory where to find images for classification')
    parser.add_argument('--num_classes', type=int, required=True,
                        help='number of classes')
    parser.add_argument('--take_top_n', type=int, default=10,
                        help='number of classes to store to the pseudo-index file')
    parser.add_argument('--bin_dir', default='bin',
                        help='directory containing checkpoints and logs folder')
    args = parser.parse_args()

    images = model_utils.get_images_from_dir(args.image_dir)
    run(images, args.num_classes, args.take_top_n, args.bin_dir, restore_all=True)
