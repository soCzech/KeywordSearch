import os.path
import sys
import struct
import argparse
import tensorflow as tf
import numpy as np

from models import network, inception_v1, model_utils

slim = tf.contrib.slim


def run(tfrecord_dir, dataset_name, num_classes, bin_dir, restore_all, calc_cov=True):
    if calc_cov:
        mean = np.zeros(num_classes, dtype=np.float)
        cov = np.zeros((num_classes, num_classes), dtype=np.float)
        confusion = np.zeros((num_classes, num_classes), dtype=np.int32)

    images, labels = network.get_batch(tfrecord_dir, dataset_name, batch_size=80,
                                       image_size=inception_v1.default_image_size, is_training=False)

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

    correct_prediction = tf.equal(tf.cast(labels, tf.int64), tf.argmax(logits, 1), name='in_top_1')
    in_top_5 = tf.nn.in_top_k(logits, labels, k=5, name='in_top_5')
    in_top_10 = tf.nn.in_top_k(logits, labels, k=10, name='in_top_10')

    """ Covariance """
    if calc_cov:
        probabilities = tf.nn.softmax(logits)

        last_mean = tf.placeholder(tf.float32, shape=num_classes)
        last_cov = tf.placeholder(tf.float32, shape=(num_classes, num_classes))

        add_to_mean = tf.add(last_mean, tf.reduce_sum(probabilities, 0))
        add_to_cov = tf.add(last_cov, tf.matmul(tf.transpose(probabilities), probabilities))

        last_conf = tf.placeholder(tf.int32, shape=num_classes)
        conf_batch = tf.contrib.metrics.confusion_matrix(tf.argmax(logits, 1), labels)
        add_to_conf = tf.add(last_conf, conf_batch)
    """ END / Covariance """

    session.run(tf.global_variables_initializer())

    if restore_all:
        model_utils.restore_model(session, bin_dir, None)
    else:
        model_utils.restore_model(session, bin_dir, inception_vars, generalist_vars)

    acc_sum, acc_top1, acc_top5, acc_top10 = 0, 0, 0, 0

    try:
        while not coord.should_stop():
            if calc_cov:
                shape, top1, top5, top10, mean, cov = session.run([
                    tf.shape(logits), tf.reduce_sum(tf.cast(correct_prediction, tf.int32)),
                    tf.reduce_sum(tf.cast(in_top_5, tf.int32)), tf.reduce_sum(tf.cast(in_top_10, tf.int32)),
                    add_to_mean, add_to_cov, add_to_conf
                ], feed_dict={last_mean: mean, last_cov: cov, last_conf: confusion})
            else:
                shape, top1, top5, top10, = session.run([tf.shape(logits),
                                                         tf.reduce_sum(tf.cast(correct_prediction, tf.int32)),
                                                         tf.reduce_sum(tf.cast(in_top_5, tf.int32)),
                                                         tf.reduce_sum(tf.cast(in_top_10, tf.int32))])
            acc_sum += shape[0]
            acc_top1 += top1
            acc_top5 += top5
            acc_top10 += top10

            sys.stdout.write('\r>> Evaluating... Processed {:d}, Top1 {:.0f}%, Top5 {:.0f}%, Top10 {:.0f}%'.format(
                acc_sum, acc_top1 / acc_sum * 100, acc_top5 / acc_sum * 100, acc_top10 / acc_sum * 100))
            sys.stdout.flush()

    except tf.errors.OutOfRangeError:
        sys.stdout.write('\r>> Evaluated. Processed {:d}, Top1 {:.0f}%, Top5 {:.0f}%, Top10 {:.0f}%\n'.format(
            acc_sum, acc_top1 / acc_sum * 100, acc_top5 / acc_sum * 100, acc_top10 / acc_sum * 100))
        sys.stdout.flush()
    finally:
        if calc_cov:
            store_mean_and_covariance(mean, cov, acc_sum, os.path.join(bin_dir, 'covariance'))
            store_confusion(confusion, os.path.join(bin_dir, 'covariance'))

        # When done, ask the threads to stop.
        coord.request_stop()

        # Wait for threads to finish.
        coord.join(threads)
        session.close()

    model_utils.write_evaluation(os.path.join(bin_dir, 'evaluation_nn.txt'),
                                 [('#Images', acc_sum, '{:16d}'), ('Top1Count', acc_top1, '{:16d}'),
                                  ('Top5Count', acc_top5, '{:16d}'), ('Top10Count', acc_top10, '{:16d}')])


def store_mean_and_covariance(mean, cov, no_images, folder):
    # E[XX^T]-E[X]E[X]^T
    mean = mean / no_images
    cov = cov / no_images - np.outer(mean, mean)

    frmt = '<'+'f'*len(mean)

    with open(os.path.join(folder, 'mean.bin'), 'wb') as f:
        f.write(struct.pack('<I', len(mean)))
        f.write(struct.pack(frmt, *mean))
    with open(os.path.join(folder, 'covariance.bin'), 'wb') as f:
        f.write(struct.pack('<I', len(mean)))
        for i in range(len(cov)):
            f.write(struct.pack(frmt, *cov[i]))


def store_confusion(conf, folder):
    frmt = '<' + 'I' * len(conf[0])
    with open(os.path.join(folder, 'confusion.bin'), 'wb') as f:
        f.write(struct.pack('<I', len(conf[0])))
        for i in range(len(conf)):
            f.write(struct.pack(frmt, *conf[i]))


# py actions/evaluate.py --tfrecord_dir=..\_test\tfrecords --filename=eval5 --num_classes=2
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--tfrecord_dir', required=True,
                        help='directory where to find tfrecord files')
    parser.add_argument('--filename', required=True,
                        help='a name of the tfrecord files')
    parser.add_argument('--num_classes', type=int, required=True,
                        help='number of classes')
    parser.add_argument('--bin_dir', default='bin',
                        help='directory containing checkpoints and logs folder')
    args = parser.parse_args()

    run(args.tfrecord_dir, args.filename, args.num_classes, args.bin_dir, restore_all=True)
