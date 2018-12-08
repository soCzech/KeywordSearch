import os
import sys
import argparse
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
import tensorflow as tf

from common_utils import input_pipeline, console
from models import network


def validate(filenames, num_classes, ckpt_dir="./"):
    """Performs validation run on a tfrecord dataset files. =
    Also calculates accuracy using multiple patches from an image.

    Args:
        filenames: Tfrecord filenames.
        num_classes: Number of classes in the softmax classification layer.
        ckpt_dir: Location where the checkpoints are stored.
    """
    use_inception = False
    use_large = True

    pt = console.ProgressTracker()
    sess = tf.Session()

    iterator = input_pipeline.make_image_patches(filenames, use_large=use_large)
    images, labels = iterator.get_next()

    """
        Network model
    """
    if use_inception:
        logits, _ = network.build_net(images, num_classes, is_training=False)
    else:
        logits, _ = network.build_nasnet(images, num_classes, is_training=False, use_large=use_large)

    """
        Results
    """
    with tf.name_scope('results'):
        labels = tf.expand_dims(labels, 0)
        correct_prediction = tf.equal(tf.cast(labels, tf.int64), tf.argmax(logits[:1], 1))

        accuracy = tf.reduce_sum(tf.cast(correct_prediction, tf.float32), name='accuracy')
        in_top_5 = tf.reduce_sum(tf.cast(tf.nn.in_top_k(logits[:1], labels, k=5), tf.float32),
                                 name='top_5_predictions')
        in_top_10 = tf.reduce_sum(tf.cast(tf.nn.in_top_k(logits[:1], labels, k=10), tf.float32),
                                  name='top_10_predictions')

        logits = tf.expand_dims(tf.reduce_mean(tf.nn.softmax(logits), axis=0), 0)
        correct_prediction = tf.equal(tf.cast(labels, tf.int64), tf.argmax(logits, 1))

        accuracy_averaged = tf.reduce_sum(tf.cast(correct_prediction, tf.float32), name='accuracy_averaged')
        in_top_5_averaged = tf.reduce_sum(tf.cast(tf.nn.in_top_k(logits, labels, k=5), tf.float32),
                                          name='top_5_predictions_averaged')
        in_top_10_averaged = tf.reduce_sum(tf.cast(tf.nn.in_top_k(logits, labels, k=10), tf.float32),
                                           name='top_10_predictions_averaged')

    sess.run(tf.global_variables_initializer())

    """
        Savers
    """
    pt.info(">> Restoring trained model.")
    saver = tf.train.Saver()
    if os.path.isdir(ckpt_dir):
        saver.restore(sess, tf.train.latest_checkpoint(ckpt_dir))
    else:
        saver.restore(sess, ckpt_dir)

    """
        Validation
    """
    pt.info(">> Validating...")

    top_acc = {
        "top_1": 0,
        "top_5": 0,
        "top_10": 0,
        "top_1_avg": 0,
        "top_5_avg": 0,
        "top_10_avg": 0
    }
    examples = 0
    while True:
        try:
            top1, top5, top10, top1_avg, top5_avg, top10_avg = sess.run([
                accuracy, in_top_5, in_top_10, accuracy_averaged, in_top_5_averaged, in_top_10_averaged
            ])
            top_acc["top_1"] += top1
            top_acc["top_5"] += top5
            top_acc["top_10"] += top10
            top_acc["top_1_avg"] += top1_avg
            top_acc["top_5_avg"] += top5_avg
            top_acc["top_10_avg"] += top10_avg
            examples += 1

            results = "Results: " + ", ".join([
                "{:8} {:.4f}%".format(name, val / examples * 100) for name, val in top_acc.items()
            ])
            pt.progress_info("Images evaluated:{:6d} | {}", [examples, results])
        except tf.errors.OutOfRangeError:
            pt.info(">> Validation completed.")
            break

    results = ["{:8} {:.4f}%".format(name, val / examples * 100) for name, val in top_acc.items()]
    pt.info("Results: " + ", ".join(results))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--val', type=str, required=True)
    parser.add_argument('--ckpt_dir', type=str, required=True,
                        help='Directory of the checkpoints.')
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        exit(1)

    val = [os.path.join(args.val, name) for name in os.listdir(args.val) if name[-9:] == ".tfrecord"]

    validate(val, num_classes=1243, ckpt_dir=args.ckpt_dir)
