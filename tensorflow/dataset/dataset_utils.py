import os
import tensorflow as tf


def get_dataset_filename(tfrecord_dir, filename, shard_id, shards):
    """
    :return: tfrecord filename
    """
    output_filename = '{}_{:05d}-of-{:05d}.tfrecord'.format(filename, shard_id, shards)
    return os.path.normpath(os.path.join(tfrecord_dir, output_filename))


def dataset_exists(tfrecord_dir, filename, shards):
    """
    :param tfrecord_dir: directory of dataset
    :param filename: core filename of dataset
    :param shards: number of parts to split dataset in
    :return: true if exists and need not to be created
    """
    for shard_id in range(shards):
        output_filename = get_dataset_filename(tfrecord_dir, filename, shard_id, shards)
        if not os.path.exists(output_filename):
            return False
    return True


def write_label_file(labels_to_class_names, dataset_dir, filename):
    """
    Writes a file with the list of class names.

    :param labels_to_class_names: A map of (integer) labels to class names.
    :param dataset_dir: The directory in which the labels file should be written.
    :param filename: The filename where the class names are written.
    """

    labels_filename = os.path.join(dataset_dir, filename)
    with open(labels_filename, 'w') as f:
        for label in labels_to_class_names:
            class_name = labels_to_class_names[label]
            f.write('{:d}:{}\n'.format(label, class_name))


def read_label_file(dataset_dir, filename):
    """
    Reads the labels file and returns a mapping from ID to class name.

    :param dataset_dir: The directory in which the labels file is found.
    :param filename: The filename where the class names are written.
    :return: A map from a label (integer) to class name.
    """

    labels_filename = os.path.join(dataset_dir, filename)
    with open(labels_filename, 'r') as f:
        lines = f.read()
    lines = lines.split('\n')
    lines = filter(None, lines)

    labels_to_class_names = {}
    for line in lines:
        index = line.index(':')
        labels_to_class_names[int(line[:index])] = line[index+1:]
    return labels_to_class_names


class ImageReader:
    """
    Helper class that provides TensorFlow image coding utilities.
    """

    def __init__(self):
        # Initializes function that decodes RGB JPEG data.
        self._decode_jpeg_data = tf.placeholder(dtype=tf.string)
        self._decode_jpeg = tf.image.decode_jpeg(self._decode_jpeg_data, channels=3)

    def read_image_dims(self, sess, image_data):
        image = self.decode_jpeg(sess, image_data)
        return image.shape[0], image.shape[1]

    def decode_jpeg(self, sess, image_data):
        image = sess.run(self._decode_jpeg,
                         feed_dict={self._decode_jpeg_data: image_data})
        assert len(image.shape) == 3
        assert image.shape[2] == 3
        return image


def get_tfrecord_files(tfrecord_dir, dataset_name):
    prefix = '{}_'.format(dataset_name)

    parts = -1
    for file in os.listdir(tfrecord_dir):
        if file.startswith(prefix) and file.endswith(".tfrecord"):
            parts = int(file[-14:-9])
            break
    if parts == -1:
        raise ValueError()

    tfrecord = '{}/{}{{:05d}}-of-{:05d}.tfrecord'.format(tfrecord_dir, prefix, parts)
    return [tfrecord.format(i) for i in range(parts)]


def get_dataset(filename_queue):
    reader = tf.TFRecordReader()

    _, serialized_example = reader.read(filename_queue)

    features = tf.parse_single_example(serialized_example, features={
        'image/height': tf.FixedLenFeature([], tf.int64),
        'image/width': tf.FixedLenFeature([], tf.int64),
        'image/encoded': tf.FixedLenFeature([], tf.string),
        'image/class/label': tf.FixedLenFeature([], tf.int64)
    })

    image = tf.image.decode_jpeg(features['image/encoded'], channels=3)
    label = tf.cast(features['image/class/label'], tf.int32)

    height = tf.cast(features['image/height'], tf.int32)
    width = tf.cast(features['image/width'], tf.int32)

    image = tf.reshape(image, [height, width, 3])

    return image, label
