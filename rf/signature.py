import os.path
import sys
import argparse
import struct
import tensorflow as tf

from models import network, inception_v1, model_utils

slim = tf.contrib.slim


def run(tfrecord_dir, dataset_name, num_classes, bin_dir):
    images, labels = network.get_batch(tfrecord_dir, dataset_name, batch_size=20,
                                       image_size=inception_v1.default_image_size, is_training=False)

    session = tf.Session()
    session.run(tf.local_variables_initializer())

    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(sess=session, coord=coord)

    """
        Network model
    """
    _, net = network.build_net(images, num_classes, scope='InceptionGeneralist', is_training=False)
    endpoint = tf.squeeze(net['AvgPool_0a_7x7'], [1, 2])

    session.run(tf.global_variables_initializer())

    inception_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='InceptionV1')
    model_utils.restore_model(session, bin_dir, inception_vars)

    filename = dataset_name + '.signatures'
    if os.path.isfile(filename):
        raise Exception(filename + ' already exists.')

    file = open(filename, 'wb')
    signature_format = '<' + 'f' * 1024

    try:
        while not coord.should_stop():
            result, true_result = session.run([endpoint, labels])

            for signature, label in zip(result, true_result):
                data = struct.pack('<I', label) + struct.pack(signature_format, *signature)
                file.write(data)
    except tf.errors.OutOfRangeError:
        print()
    finally:
        file.close()
        # When done, ask the threads to stop.
        coord.request_stop()

        # Wait for threads to finish.
        coord.join(threads)
        session.close()


if __name__ == '__main__':
    run('../_test/tfrecords', 'test_all_but5', 2, 'bin')
