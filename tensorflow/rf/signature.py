import os.path
import sys
import argparse
import struct
import tensorflow as tf

from models import network, inception_v1, model_utils


signature_size = 1024
signature_format = '<' + 'f' * signature_size


def run(tfrecord_dir, dataset_name, signature_dir, num_classes, bin_dir):
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

    filename = os.path.join(os.path.normpath(signature_dir), '{}.signatures'.format(dataset_name))
    if os.path.isfile(filename):
        raise Exception(filename + ' already exists.')

    file = open(filename, 'wb')

    i = 0
    try:
        while not coord.should_stop():
            sys.stdout.write('\r>> Creating signatures... Processed {:d} images.'.format(i))
            sys.stdout.flush()

            result, true_result = session.run([endpoint, labels])

            for signature, label in zip(result, true_result):
                data = struct.pack('<I', label) + struct.pack(signature_format, *signature)
                file.write(data)

            i += len(result)

    except tf.errors.OutOfRangeError:
        sys.stdout.write('\rSignatures created.\n')
        sys.stdout.flush()
    finally:
        file.close()
        # When done, ask the threads to stop.
        coord.request_stop()

        # Wait for threads to finish.
        coord.join(threads)
        session.close()

# py rf/signature.py --tfrecord_dir=..\_test\tfrecords --filename=test_all_but5 --signature_dir=..\_test\signatures
# --num_classes=2
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--tfrecord_dir', required=True,
                        help='directory where to find tfrecord files')
    parser.add_argument('--filename', required=True,
                        help='a name of the tfrecord files')
    parser.add_argument('--signature_dir', required=True,
                        help='directory where to store signatures')
    parser.add_argument('--num_classes', type=int, required=True,
                        help='number of classes')
    parser.add_argument('--bin_dir', default='bin',
                        help='directory containing checkpoints and logs folder')
    args = parser.parse_args()

    run(args.tfrecord_dir, args.filename, args.signature_dir, args.num_classes, args.bin_dir)
