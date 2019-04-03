import os
import sys
import time
import argparse
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
import tensorflow as tf
from datetime import datetime

from common_utils import input_pipeline, console
from models import network


def train(filenames, batch_size, num_classes, learning_rate=0.0001, train_all=False, ckpt_dir="./",
          no_epochs=10, batches_per_epoch=1000, batches_per_validation=100, decay_every_n_steps=10000):
    """Trains a neural network for given number of epochs.

    Args:
        filenames: Dictionary with 'train' and 'validation' key containing names of tfrecord files.
        batch_size: Batch size to use.
        num_classes: Number of classes in the softmax classification layer.
        learning_rate: Initial learning rate.
        train_all: True if the whole network should be trained, otherwise only the last layer will be trained.
        ckpt_dir: Location where the checkpoints are stored.
        no_epochs: Number of epoch to run for.
        batches_per_epoch: Number of batches per epoch.
        batches_per_validation: Number of batches to run from the validation dataset after each epoch.
        decay_every_n_steps: Lower learning rate each n steps.
    """

    use_inception = False
    use_large = True
    sleep_sometimes = False

    pt = console.ProgressTracker()
    sess = tf.Session()

    with tf.name_scope("Dataset"):
        train_iterator = input_pipeline.make_batch(filenames["train"], batch_size, is_training=True, use_large=use_large)
        val_iterator = input_pipeline.make_batch(filenames["validation"], batch_size, is_training=False, use_large=use_large)

        train_iterator_handle = sess.run(train_iterator.string_handle())
        val_iterator_handle = sess.run(val_iterator.string_handle())

        handle = tf.placeholder(tf.string, shape=[])
        iterator = tf.data.Iterator.from_string_handle(handle, output_types=train_iterator.output_types,
                                                       output_shapes=train_iterator.output_shapes)

        images, labels = iterator.get_next()

    """
        Network model
    """
    if use_inception:
        logits, _ = network.build_net(images, num_classes, is_training=True)
    else:
        logits, _ = network.build_nasnet(images, num_classes, is_training=True, use_large=use_large)

    inception_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES)
    logit_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='Logits' if use_inception else 'final_layer')
    for var in logit_vars:
        inception_vars.remove(var)

    """
        Losses
    """
    with tf.name_scope('losses'):
        labels = tf.one_hot(labels, num_classes, dtype=tf.float32) * 0.9 + (0.1 / num_classes)
        diff_logits = tf.nn.softmax_cross_entropy_with_logits_v2(labels=labels, logits=logits)
        cross_entropy_loss = tf.reduce_mean(diff_logits)

    """
        Train
    """
    with tf.name_scope('train'):
        global_step = tf.Variable(0, name='global_step', trainable=False)

        learning_rate = tf.train.exponential_decay(learning_rate, global_step, decay_every_n_steps, 0.5,
                                                   staircase=True, name='exponential_decay_learning_rate')

        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
        with tf.control_dependencies(update_ops):
            training = tf.train.RMSPropOptimizer(learning_rate, epsilon=1.0).minimize(
                cross_entropy_loss,
                global_step=global_step,
                var_list=None if train_all else logit_vars
            )

    logit_vars += tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='train/global_step')

    """
        Results
    """
    with tf.name_scope('results'):
        logits_shape = tf.shape(logits, name="batch_shape")
        correct_prediction = tf.equal(tf.cast(labels, tf.int64), tf.argmax(logits, 1))
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32), name='accuracy')

        in_top_5 = tf.reduce_mean(tf.cast(tf.nn.in_top_k(logits, labels, k=5), tf.float32), name='top_5_predictions')
        in_top_10 = tf.reduce_mean(tf.cast(tf.nn.in_top_k(logits, labels, k=10), tf.float32), name='top_10_predictions')

    """
        Summary
    """
    log_dir = os.path.normpath(os.path.join("../logs", datetime.now().strftime('%Y-%m-%d_%H%M%S')))

    summaries = [tf.summary.scalar('train/loss/cross_entropy', cross_entropy_loss),
                 tf.summary.scalar('train/predictions/top_1', accuracy),
                 tf.summary.scalar('train/predictions/top_5', in_top_5),
                 tf.summary.scalar('train/predictions/top_10', in_top_10),
                 tf.summary.scalar('train/learning_rate', learning_rate)]
    summaries = tf.summary.merge(summaries)
    summary_writer = tf.summary.FileWriter(log_dir, sess.graph, flush_secs=100)

    sess.run(tf.global_variables_initializer())

    """
        Savers
    """
    if train_all:
        pt.info(">> Restoring trained model.")
        saver = tf.train.Saver(var_list=inception_vars + logit_vars, max_to_keep=30)
        saver.restore(sess, tf.train.latest_checkpoint(ckpt_dir))
    else:
        pt.info(">> Restoring default ILSVRC model.")
        saver = tf.train.Saver(var_list=inception_vars)
        saver.restore(sess, os.path.join(ckpt_dir, 'inception_v1.ckpt' if use_inception else 'nasnet.ckpt'))
        saver = tf.train.Saver(var_list=inception_vars + logit_vars, max_to_keep=30)

    for epoch in range(no_epochs):
        pt.info(">> Training {:d} of {:d} epochs.".format(epoch + 1, no_epochs))
        pt.reset(batches_per_epoch)

        for i in range(batches_per_epoch):
            _, summary = sess.run([training, summaries], feed_dict={handle: train_iterator_handle})
            if i % 10 == 9:
                gs = sess.run(global_step)
                summary_writer.add_summary(summary, gs)
            if sleep_sometimes and i % 200 == 199:
                time.sleep(20)
            pt.increment()

        # validation
        pt.info(">> Validating...")
        pt.reset(batches_per_validation)

        top_acc = {
            "top_1": 0,
            "top_5": 0,
            "top_10": 0
        }
        examples = 0
        for _ in range(batches_per_validation):
            top1, top5, top10, shape = sess.run([accuracy, in_top_5, in_top_10, logits_shape],
                                                feed_dict={handle: val_iterator_handle})
            top_acc["top_1"] += top1
            top_acc["top_5"] += top5
            top_acc["top_10"] += top10
            examples += shape[0]

            pt.increment()

        results = []
        gs = sess.run(global_step)
        for name, val in top_acc.items():
            summary = tf.Summary()
            summary.value.add(tag="val/predictions/" + name, simple_value=val/batches_per_validation)
            results.append("{:8} {:.4f}%".format(name, val/batches_per_validation * 100))
            summary_writer.add_summary(summary, gs)

        pt.info("Results: " + ", ".join(results))

        saver.save(sess, os.path.join(
            ckpt_dir, ("inception" if use_inception else "nasnet") + "_retrained-{:02d}-{:.2f}.ckpt".format(
                epoch + 1, top_acc["top_1"] / batches_per_validation * 100
            )
        ), global_step=global_step)

    summary_writer.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--trn', type=str, required=True)
    parser.add_argument('--val', type=str, required=True)
    parser.add_argument('--ckpt_dir', type=str, required=True,
                        help='Directory of the checkpoints.')
    parser.add_argument('--lr', type=float, default=0.001, help="Initial learning rate")
    parser.add_argument('--train_all', action='store_true', default=False,
                        help='Train whole network instead of the last layer')
    parser.add_argument('--no_epochs', type=int, default=30, help="Number of epochs")
    parser.add_argument('--decay_lr_every_steps', type=int, default=10000)
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        exit(1)

    trn = [os.path.join(args.trn, name) for name in os.listdir(args.trn) if name[-9:] == ".tfrecord"]
    val = [os.path.join(args.val, name) for name in os.listdir(args.val) if name[-9:] == ".tfrecord"]

    # train({"train": trn, "validation": val},
    #       batch_size=64, num_classes=1150, learning_rate=0.0001, train_all=False, ckpt_dir=ckpt_dir,
    #       no_epochs=30, batches_per_epoch=500, batches_per_validation=100, decay_every_n_steps=7500)

    train({"train": trn, "validation": val},
          batch_size=32, num_classes=1243, learning_rate=args.lr, train_all=args.train_all,
          ckpt_dir=args.ckpt_dir, no_epochs=args.no_epochs, decay_every_n_steps=args.decay_lr_every_steps)
