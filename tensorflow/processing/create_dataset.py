import os
import random
import math
import argparse
import tensorflow as tf

from common_utils import console, input_pipeline
# from processing import create_labels


def convert_dataset(raw_dir, tfrecord_dir, dataset_name, shards, skip_first=0., take=-1):
    """Converts all images in given directory to tfrecord files. Also creates the label file.

    Args:
        raw_dir: A directory containing a set of subdirectories representing class names.
            Each subdirectory should contain PNG or JPG encoded images.
        tfrecord_dir: A place to store converted images.
        dataset_name: A name for the new files.
        shards: Number of parts to split dataset to.
        skip_first: Number of images to skip in each class.
        take: Number of images to take from each class, -1 means all.
    """
    pt = console.ProgressTracker()
    tfrecord_dir = os.path.normpath(tfrecord_dir)

    if dataset_exists(tfrecord_dir, dataset_name, shards):
        pt.info('Dataset files already exist. Exiting without re-creating them.')
        return

    if not os.path.isdir(tfrecord_dir):
        os.mkdir(tfrecord_dir)

    raw_dir = os.path.normpath(raw_dir)

    photo_filenames, class_names = get_filenames_and_classes(raw_dir, skip_first, take)
    pt.info('{} images found to convert in {} classes.'.format(len(photo_filenames), len(class_names)))
    pt.info('Shuffling photos.')

    class_names_to_ids = dict(zip(class_names, range(len(class_names))))

    random.seed(42)
    random.shuffle(photo_filenames)

    convert_photos(photo_filenames, tfrecord_dir, dataset_name, shards, class_names_to_ids)

    # pt.info('Creating label file.')
    # create_labels.create_labels(class_names_to_ids, os.path.join(tfrecord_dir, '{}_labels'.format(dataset_name)))
    pt.info('Dataset converted.')


def convert_photos(images, tfrecord_dir, dataset_name, shards, class_names_dict):
    """Stores images into tfrecord files.

    Args:
        images: A list of images to convert.
        tfrecord_dir: A place to store converted images.
        dataset_name: A name for the new files.
        shards: Number of parts to split dataset to.
        class_names_dict: Dictionary mapping class names to ids.
    """

    def _bytes_feature(value):
        return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

    def _int64_feature(value):
        return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))

    pt = console.ProgressTracker()
    pt.info("Converting photos...")
    pt.reset(len(images))

    num_per_shard = int(math.ceil(len(images) / float(shards)))

    image_reader = input_pipeline.ImageReader()
    with tf.Session() as sess:

        for shard_id in range(shards):
            output_filename = get_dataset_filename(tfrecord_dir, dataset_name, shard_id, shards)

            with tf.python_io.TFRecordWriter(output_filename) as writer:
                start_ndx = shard_id * num_per_shard
                end_ndx = min((shard_id+1) * num_per_shard, len(images))

                for i in range(start_ndx, end_ndx):
                    pt.progress_info('>> Converting image {:d}/{:d} shard {:d}', (
                        i + 1, len(images), shard_id,
                    ), i, len(images))

                    image_data = tf.gfile.FastGFile(images[i], 'rb').read()
                    # https://github.com/tensorflow/models/blob/master/slim/datasets/download_and_convert_flowers.py
                    try:
                        height, width = image_reader.read_image_dims(sess, image_data)
                    except tf.errors.InvalidArgumentError:
                        pt.error('Skipping {} for error.'.format(images[i]))
                        continue

                    class_name = os.path.basename(os.path.dirname(images[i]))
                    class_id = class_names_dict[class_name]

                    example = tf.train.Example(features=tf.train.Features(feature={
                        'image/encoded': _bytes_feature(image_data),
                        'image/class/label': _int64_feature(class_id),
                        'image/height': _int64_feature(height),
                        'image/width': _int64_feature(width)
                    }))

                    writer.write(example.SerializeToString())
    pt.info('Photos converted.')


def get_filenames_and_classes(dataset_dir, skip_first, take):
    """Reads all images in given directory.

    Args:
        dataset_dir: A directory containing a set of subdirectories representing
            class names. Each subdirectory should contain PNG or JPG encoded images.
        skip_first: Number of images to skip in each class.
        take: Number of images to take from each class, -1 means all.

    Returns:
        A list of image file paths, relative to dataset_dir and the list of
        subdirectories, representing class names.
    """

    class_names = []
    photo_filenames = []
    pt = console.ProgressTracker()
    pt.info("Reading files...")

    classes = os.listdir(dataset_dir)
    pt.reset(len(classes))
    for class_dir in classes:
        class_path = os.path.join(dataset_dir, class_dir)
        if os.path.isdir(class_path):
            photos = []
            for image in os.listdir(class_path):
                photos.append(os.path.join(dataset_dir, class_dir, image))
            photos = sorted(photos)

            if isinstance(skip_first, float):
                to_skip = int(round(len(photos) * skip_first))
                to_take = int(round(len(photos) * take))
            else:
                to_skip = skip_first
                to_take = take

            if to_take > 0:
                photo_filenames.extend(photos[to_skip:to_skip+to_skip])
            else:
                photo_filenames.extend(photos[to_skip:])

            class_names.append(class_dir)
        pt.increment()

    return photo_filenames, sorted(class_names)


def get_dataset_filename(tfrecord_dir, filename, shard_id, shards):
    """ Constructs filename from given arguments.

    Returns:
        tfrecord filename
    """
    output_filename = '{}_{:05d}-of-{:05d}.tfrecord'.format(filename, shard_id, shards)
    return os.path.normpath(os.path.join(tfrecord_dir, output_filename))


def dataset_exists(tfrecord_dir, filename, shards):
    """Checks if specified dataset exists.

    Args:
        tfrecord_dir: directory of dataset
        filename: core filename of dataset
        shards: number of parts to split dataset in

    Returns:
        true if exists and need not to be created
    """
    for shard_id in range(shards):
        output_filename = get_dataset_filename(tfrecord_dir, filename, shard_id, shards)
        if not os.path.exists(output_filename):
            return False
    return True


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
    parser.add_argument('--skip_first', type=float, default=0.,
                        help='skip first n images from each class')
    parser.add_argument('--take', type=float, default=-1,
                        help='number of images to take from each class')
    args = parser.parse_args()

    convert_dataset(args.dataset_dir, args.tfrecord_dir, args.filename, args.parts, args.skip_first, args.take)
