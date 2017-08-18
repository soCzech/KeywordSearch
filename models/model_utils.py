import os
from datetime import datetime
import tensorflow as tf


def _get_ckpt_path(bin_dir):
    return 'model_v1.ckpt', os.path.normpath(os.path.join(bin_dir, 'checkpoints'))


def restore_model(session, bin_dir, inception_vars, generalist_vars=None):
    ckpt_name, ckpt_dir = _get_ckpt_path(bin_dir)

    saver1 = tf.train.Saver(var_list=inception_vars)
    saver1.restore(session, os.path.join(ckpt_dir, 'inception_v1.ckpt'))

    if generalist_vars is None:
        return

    saver2 = tf.train.Saver(var_list=generalist_vars)
    for name in os.listdir(ckpt_dir):
        if os.path.isfile(os.path.join(ckpt_dir, name)) and ckpt_name in name:
            saver2.restore(session, tf.train.latest_checkpoint(ckpt_dir))  # TODO: fix - takes random last checkpoint
    return saver2


def save_model(saver, session, bin_dir, global_step):
    ckpt_name, ckpt_dir = _get_ckpt_path(bin_dir)
    saver.save(session, os.path.join(ckpt_dir, ckpt_name), global_step=global_step)


def get_images_from_dir(directory):
    directory = os.path.normpath(directory)
    return [os.path.join(directory, filename) for filename in os.listdir(directory)]


def write_evaluation(filename, results):
    exists = os.path.isfile(filename)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S ')

    with open(filename, 'a') as f:
        if not exists:
            f.write(' ' * 20 + ', '.join(['{:10}'.format(x) for x, _ in results]) + '\n')
        f.write(timestamp + ', '.join(['{:10d}'.format(x) for _, x in results]) + '\n')
