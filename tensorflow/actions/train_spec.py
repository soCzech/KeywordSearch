import os
import datetime
import argparse
import time

import tensorflow as tf
from models import network, inception_v1, model_utils

import sys

slim = tf.contrib.slim


def run(tfrecord_dir, dataset_name, batch_size, num_classes, bin_dir, learning_rate=0.01,
        number_of_iterations=100000, save_each=2000, restore_all=False, train_all=False):

    images, labels = network.get_batch(tfrecord_dir, dataset_name, batch_size=batch_size,
                                       image_size=inception_v1.default_image_size, is_training=True)
    labels = tf.one_hot(labels, num_classes, name='OneHotLabels')

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

    logits_specialist, _ = network.build_net(images, num_classes, scope='InceptionSpecialist',
                                             is_training=True, base_scope='InceptionV1Specialist')

    inception_specialist_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='InceptionV1Specialist')
    specialist_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='InceptionSpecialist')

    """
        Losses
    """

    temperature = 20
    labels_smoothed = tf.nn.softmax(logits/temperature)

    @tf.RegisterGradient("ScaleGradient")
    def _const_mul_grad(_, grad):
        return temperature * temperature * grad

    g = tf.get_default_graph()
    with g.gradient_override_map({"Identity": "ScaleGradient"}):
        logits_specialist_smoothed = tf.identity(logits_specialist, name="Identity")

    with tf.name_scope('losses'):
        with tf.name_scope('SoftTarget'):
            diff_logits_s = tf.nn.softmax_cross_entropy_with_logits(labels=labels_smoothed,
                                                                    logits=logits_specialist_smoothed/temperature)
            cross_entropy_logits_s = tf.reduce_mean(diff_logits_s)
            tf.summary.scalar('logits', cross_entropy_logits_s)
        with tf.name_scope('OneHot'):
            diff_logits = tf.nn.softmax_cross_entropy_with_logits(labels=labels, logits=logits_specialist)
            cross_entropy_logits = tf.reduce_mean(diff_logits)
            tf.summary.scalar('logits', cross_entropy_logits)
        loss = cross_entropy_logits * 0.2 + cross_entropy_logits_s * 0.8

    tf.contrib.framework.init_from_checkpoint(tf.train.latest_checkpoint(os.path.join(bin_dir, 'checkpoints')),
                                              {'InceptionV1/': 'InceptionV1Specialist/',
                                               'InceptionGeneralist/': 'InceptionSpecialist/'})

    # print(tf.contrib.framework.list_variables(tf.train.latest_checkpoint(os.path.join(bin_dir, 'checkpoints'))))
    """
        Train
    """
    with tf.name_scope('train'):
        global_step = tf.Variable(0, name='global_step', trainable=False)

        decay_steps = int(100000 / batch_size)
        learning_rate = tf.train.exponential_decay(learning_rate, global_step, decay_steps, 0.94,
                                                   staircase=True, name='exponential_decay_learning_rate')
        tf.summary.scalar('learning_rate', learning_rate)

        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
        with tf.control_dependencies(update_ops):
            training = tf.train.AdamOptimizer(learning_rate, beta1=0.9, beta2=0.999).minimize(
                loss,
                global_step=global_step,
                var_list=specialist_vars + inception_specialist_vars if train_all else specialist_vars
            )

    specialist_vars += tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope='train/global_step')

    """
        Results
    """
    with tf.name_scope('results'):
        with tf.name_scope('generalist'):
            with tf.name_scope('correct_prediction'):
                correct_prediction = tf.equal(tf.argmax(labels, 1), tf.argmax(logits, 1))
            with tf.name_scope('accuracy'):
                accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
            tf.summary.scalar('accuracy', accuracy)
        with tf.name_scope('specialist'):
            with tf.name_scope('correct_prediction'):
                correct_prediction_s = tf.equal(tf.argmax(labels, 1), tf.argmax(logits_specialist, 1))
            with tf.name_scope('accuracy'):
                accuracy_s = tf.reduce_mean(tf.cast(correct_prediction_s, tf.float32))
            tf.summary.scalar('accuracy', accuracy_s)

    """
        Summary
    """
    log_dir = os.path.normpath(os.path.join('E:/logs', datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')))
    summary = tf.summary.merge_all()
    train_writer = tf.summary.FileWriter(log_dir, session.graph, flush_secs=100)

    session.run(tf.global_variables_initializer())

    """
        Savers
    """

    all_saver = tf.train.Saver(var_list=inception_vars + generalist_vars)
    all_saver.restore(session, tf.train.latest_checkpoint(os.path.join(bin_dir, 'checkpoints')))

    # if restore_all:
    #     saver = model_utils.restore_model(session, bin_dir, None)
    # else:
    #     saver = model_utils.restore_model(session, bin_dir, inception_vars, generalist_vars, train_all=train_all)

    for i in range(number_of_iterations):
        s, _, g_step = session.run([summary, training, global_step])
        train_writer.add_summary(s, i)
        sys.stdout.write('\r>> Training... Batch #{:d}'.format(g_step))
        sys.stdout.flush()

        if i % save_each == save_each - 1:  # Record execution stats
            model_utils.save_model(saver, session, bin_dir, global_step)
        if i % 200 == 199:
            sys.stdout.write('\r>> Sleeping... Batch #{:d}'.format(g_step))
            sys.stdout.flush()
            time.sleep(20)

    sys.stdout.write('\r>> Training completed.\n')
    sys.stdout.flush()

    train_writer.close()
    coord.request_stop()
    coord.join(threads)


# py actions/train.py --tfrecord_dir=..\_test\tfrecords --filename=test_all_but5 --num_classes=2
# --learning_rate=0.0001
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
    parser.add_argument('--batch_size', type=int, default=20,
                        help='batch size')
    parser.add_argument('--learning_rate', type=float, default=0.01,
                        help='initial learning rate (exponential decay is implemented)')
    args = parser.parse_args()

    run(args.tfrecord_dir, args.filename, args.batch_size, args.num_classes, args.bin_dir, args.learning_rate,
        restore_all=True, train_all=True)
