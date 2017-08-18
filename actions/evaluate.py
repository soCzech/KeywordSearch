import os.path
import sys
import argparse
import tensorflow as tf

from models import network, inception_v1, model_utils

slim = tf.contrib.slim


def run(tfrecord_dir, dataset_name, num_classes, bin_dir):
    images, labels = network.get_batch(tfrecord_dir, dataset_name, batch_size=3,
                                       image_size=inception_v1.default_image_size, is_training=False)

    session = tf.Session()
    session.run(tf.local_variables_initializer())

    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(sess=session, coord=coord)

    """
        Network model
    """
    logits, _ = network.build_net(images, num_classes, scope='InceptionGeneralist', is_training=True)

    inception_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='InceptionV1')
    generalist_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='InceptionGeneralist')

    """
        Savers
    """

    # timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
    # log_dir = '{}/{}'.format('bin/logs', timestamp)
    # train_writer = tf.summary.FileWriter(log_dir + '/test', session.graph, flush_secs=10)

    correct_prediction = tf.equal(tf.cast(labels, tf.int64), tf.argmax(logits, 1), name='in_top_1')
    # accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
    # tf.summary.scalar('in_top_1', accuracy)

    in_top_5 = tf.nn.in_top_k(logits, labels, k=5, name='in_top_5')
    # tf.summary.scalar('in_top_5', tf.reduce_mean(tf.cast(in_top_5, tf.float32)))
    in_top_10 = tf.nn.in_top_k(logits, labels, k=10, name='in_top_10')
    # tf.summary.scalar('in_top_10', tf.reduce_mean(tf.cast(in_top_10, tf.float32)))

    session.run(tf.global_variables_initializer())

    model_utils.restore_model(session, bin_dir, inception_vars, generalist_vars)

    acc_sum, acc_top1, acc_top5, acc_top10 = 0, 0, 0, 0

    try:
        while not coord.should_stop():
            shape, top1, top5, top10 = session.run([tf.shape(labels),
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
        sys.stdout.write('\r>> Evaluated. Processed {:d}, Top1 {:.0f}%, Top5 {:.0f}%, Top10 {:.0f}%'.format(
            acc_sum, acc_top1 / acc_sum * 100, acc_top5 / acc_sum * 100, acc_top10 / acc_sum * 100))
        sys.stdout.flush()
    finally:
        # When done, ask the threads to stop.
        coord.request_stop()

        # Wait for threads to finish.
        coord.join(threads)
        session.close()

    model_utils.write_evaluation(os.path.join(bin_dir, 'evaluation.txt'),
                                 [('#Images', acc_sum), ('Top1Acc', acc_top1), ('Top5Acc', acc_top5),
                                  ('Top10Acc', acc_top10)])


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

    run(args.tfrecord_dir, args.filename, args.num_classes, args.bin_dir)
