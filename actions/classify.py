import argparse
import tensorflow as tf
from models import network, model_utils, inception_v1


def run(filenames, num_classes, bin_dir):
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
    top_values, top_indices = tf.nn.top_k(probabilities, k=min(5, num_classes), sorted=True)

    session.run(tf.global_variables_initializer())

    model_utils.restore_model(session, bin_dir, inception_vars, generalist_vars)

    try:
        while not coord.should_stop():
            r_key, r_image, r_top_v, r_top_i = session.run([key, image, top_values, top_indices])

            print(str(r_key) + ':  indices ' + str(r_top_i) + ', values ' + str(r_top_v))

    except tf.errors.OutOfRangeError:
        print('Done')
    finally:
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
