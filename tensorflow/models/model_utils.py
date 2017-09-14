import os
from datetime import datetime
import tensorflow as tf


def _get_ckpt_path(bin_dir):
    return 'model_v1.ckpt', os.path.normpath(os.path.join(bin_dir, 'checkpoints'))


def restore_model(session, bin_dir, inception_vars, generalist_vars=None, train_all=False):
    """
    Restores model to its latest state and returns saver

    :param session: instance of the tf session
    :param bin_dir: location of a checkpoints directory
    :param inception_vars: variables of a network without the last layer,
        if None saver tries to restore the whole network from one checkpoint file
    :param generalist_vars: variables of the last layer,
        if None saver does not restore the last layer
    :param train_all: restores the network from two checkpoints but returns one saver for the whole network
    :returns a saver, to be used for saving a network (or only the last layer of the network)
    """
    ckpt_name, ckpt_dir = _get_ckpt_path(bin_dir)

    if inception_vars is None:
        all_saver = tf.train.Saver()
        all_saver.restore(session, tf.train.latest_checkpoint(ckpt_dir))
        return all_saver

    saver1 = tf.train.Saver(var_list=inception_vars)
    saver1.restore(session, os.path.join(ckpt_dir, 'inception_v1.ckpt'))

    if generalist_vars is None:
        return

    saver2 = tf.train.Saver(var_list=generalist_vars)
    for name in os.listdir(ckpt_dir):
        if os.path.isfile(os.path.join(ckpt_dir, name)) and ckpt_name in name:
            saver2.restore(session, tf.train.latest_checkpoint(ckpt_dir))  # TODO: fix - takes random last checkpoint
    if train_all:
        return tf.train.Saver()
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
            f.write(' ' * 20 + ', '.join(['{:>16}'.format(x) for x, _, _ in results]) + '\n')
        f.write(timestamp + ', '.join([frmt.format(x) for _, x, frmt in results]) + '\n')
