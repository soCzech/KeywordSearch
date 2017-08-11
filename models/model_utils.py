import os
import tensorflow as tf


def _get_ckpt_path(bin_dir):
    return 'model_v1.ckpt', os.path.normpath(os.path.join(bin_dir, 'checkpoints'))


def restore_model(session, bin_dir, inception_vars, generalist_vars):
    ckpt_name, ckpt_dir = _get_ckpt_path(bin_dir)

    saver1 = tf.train.Saver(var_list=inception_vars)
    saver1.restore(session, os.path.join(ckpt_dir, 'inception_v1.ckpt'))
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
