import argparse
import os
import sys
import struct
import tensorflow as tf
from models import network, model_utils, inception_v1


def run(filenames, num_classes, bin_dir):
    top_number = min(5, num_classes)

    key, image = network.get_image_as_batch(filenames, inception_v1.default_image_size)

    session = tf.Session()
    session.run(tf.local_variables_initializer())

    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(sess=session, coord=coord)

    """
        Network model
    """
    logits, _ = network.build_net(image, num_classes, scope='InceptionGeneralist', is_training=False)

    inception_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='InceptionV1')
    generalist_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='InceptionGeneralist')

    probabilities = tf.nn.softmax(logits, name='Probability')
    top_values, top_indices = tf.nn.top_k(probabilities, k=top_number, sorted=True)

    session.run(tf.global_variables_initializer())

    model_utils.restore_model(session, bin_dir, inception_vars, generalist_vars)

    file = open('files.pseudo-index', 'ab')

    indices_format = '<' + 'I' * top_number
    values_format = '<' + 'f' * top_number

    i = 0
    try:
        while not coord.should_stop():
            r_key, r_image, r_top_v, r_top_i = session.run([key, image, tf.squeeze(top_values), tf.squeeze(top_indices)])

            _, filename = os.path.split(r_key)
            file_id = int(filename[:-4])

            data = struct.pack(indices_format, *r_top_i) + struct.pack(values_format, *r_top_v)

            file.write(struct.pack('<I', file_id))
            file.write(data)

            i += 1
            sys.stdout.write('\r>> Classifying... {} ({:d}/{:d})'.format(filename, i, len(filenames)))
            sys.stdout.flush()
    except tf.errors.OutOfRangeError:
        sys.stdout.write('\r>> Classification completed.\n')
        sys.stdout.flush()
    finally:
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
    parser.add_argument('--bin_dir', default='bin',
                        help='directory containing checkpoints and logs folder')
    args = parser.parse_args()

    images = model_utils.get_images_from_dir(args.image_dir)
    run(images, args.num_classes, args.bin_dir)
