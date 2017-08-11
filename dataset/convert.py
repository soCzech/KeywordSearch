import os
import random
import sys
import math
import argparse

import tensorflow as tf
import dataset.dataset_utils as dataset_utils


def convert_dataset(raw_dir, tfrecord_dir, dataset_name, shards, skip_first=0, take=-1):
    """
    Converts images to tfrecord files.

    :param raw_dir: A directory containing a set of subdirectories representing
        class names. Each subdirectory should contain PNG or JPG encoded images.
    :param tfrecord_dir: A place to store converted images.
    :param dataset_name: A name for the new files.
    :param shards: Number of parts to split dataset to.
    :param skip_first: Number of images to skip in each class.
    :param take: Number of images to take from each class, -1 means all.
    """
    tfrecord_dir = os.path.normpath(tfrecord_dir)

    if dataset_utils.dataset_exists(tfrecord_dir, dataset_name, shards):
        sys.stdout.write('\rDataset files already exist. Exiting without re-creating them.\n')
        sys.stdout.flush()
        return

    if not os.path.isdir(tfrecord_dir):
        os.mkdir(tfrecord_dir)

    raw_dir = os.path.normpath(raw_dir)

    photo_filenames, class_names = get_filenames_and_classes(raw_dir, skip_first, take)
    sys.stdout.write('\r{} images found to convert in {} classes.\n'.format(len(photo_filenames), len(class_names)))
    sys.stdout.write('\rShuffling photos.')
    sys.stdout.flush()

    class_names_to_ids = dict(zip(class_names, range(len(class_names))))

    random.seed(42)
    random.shuffle(photo_filenames)

    convert_photos(photo_filenames, tfrecord_dir, dataset_name, shards, class_names_to_ids)

    labels_to_class_names = dict(zip(range(len(class_names)), class_names))
    dataset_utils.write_label_file(labels_to_class_names, tfrecord_dir, '{}_labels.txt'.format(dataset_name))

    sys.stdout.write('\rDataset converted.\n')
    sys.stdout.flush()


def convert_photos(images, tfrecord_dir, dataset_name, shards, class_names_dict):
    """
    :param images: A list of images to convert.
    :param tfrecord_dir:  A place to store converted images.
    :param dataset_name: A name for the new files.
    :param shards: Number of parts to split dataset to.
    :param class_names_dict: Dictionary mapping class names to ids.
    """

    def _bytes_feature(value):
        return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

    def _int64_feature(value):
        return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))

    num_per_shard = int(math.ceil(len(images) / float(shards)))

    image_reader = dataset_utils.ImageReader()
    with tf.Session() as sess:

        for shard_id in range(shards):
            output_filename = dataset_utils.get_dataset_filename(tfrecord_dir, dataset_name, shard_id, shards)

            with tf.python_io.TFRecordWriter(output_filename) as writer:
                start_ndx = shard_id * num_per_shard
                end_ndx = min((shard_id+1) * num_per_shard, len(images))

                for i in range(start_ndx, end_ndx):
                    sys.stdout.write('\r>> Converting image {:d}/{:d} shard {:d}'.format(i + 1, len(images), shard_id))
                    sys.stdout.flush()

                    image_data = tf.gfile.FastGFile(images[i], 'r').read()
                    # https://github.com/tensorflow/models/blob/master/slim/datasets/download_and_convert_flowers.py
                    height, width = image_reader.read_image_dims(sess, image_data)

                    class_name = os.path.basename(os.path.dirname(images[i]))
                    class_id = class_names_dict[class_name]

                    example = tf.train.Example(features=tf.train.Features(feature={
                        'image/encoded': _bytes_feature(image_data),
                        'image/class/label': _int64_feature(class_id),
                        'image/height': _int64_feature(height),
                        'image/width': _int64_feature(width)
                    }))

                    writer.write(example.SerializeToString())

    sys.stdout.write('\r')
    sys.stdout.flush()


def get_filenames_and_classes(dataset_dir, skip_first, take):
    """
    :param dataset_dir: A directory containing a set of subdirectories representing
        class names. Each subdirectory should contain PNG or JPG encoded images.
    :param skip_first: Number of images to skip in each class.
    :param take: Number of images to take from each class, -1 means all.
    :return: A list of image file paths, relative to dataset_dir and the list of
        subdirectories, representing class names.
    """

    class_names = []
    photo_filenames = []

    for class_dir in os.listdir(dataset_dir):
        sys.stdout.write('\rFinding photos in class {}.'.format(class_dir))
        sys.stdout.flush()

        class_path = os.path.join(dataset_dir, class_dir)
        if os.path.isdir(class_path):
            photos = []
            for image in os.listdir(class_path):
                photos.append(os.path.join(dataset_dir, class_dir, image))
            photos = sorted(photos)

            if take > 0:
                photo_filenames.extend(photos[skip_first:skip_first+take])
            else:
                photo_filenames.extend(photos[skip_first:])
            class_names.append(class_dir)

    return photo_filenames, sorted(class_names)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset_dir', required=True,
                        help='directory of folders named by class names, each containing samples of a class')
    parser.add_argument('--tfrecord_dir', required=True,
                        help='directory to store tfrecord files to')
    parser.add_argument('--filename', required=True,
                        help='name for tfrecord files')
    parser.add_argument('--parts', type=int, default=1,
                        help='number of files to split dataset to')
    parser.add_argument('--skip_first', type=int, default=0,
                        help='skip first n images from each class')
    parser.add_argument('--take', type=int, default=-1,
                        help='number of images to take from each class')
    args = parser.parse_args()

    convert_dataset(args.dataset_dir, args.tfrecord_dir, args.filename, args.parts, args.skip_first, args.take)
