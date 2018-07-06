import tensorflow as tf

from models import inception_preprocessing


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


class ImageParser:

    def __init__(self, is_training, make_patches=False):
        self.is_training = is_training
        self.width = 224
        self.height = 224
        self.make_patches = make_patches

    def __call__(self, serialized_example):
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
        if self.make_patches:
            processed_image = _preprocess_with_patches(image, self.height, self.width)
        else:
            processed_image = inception_preprocessing.preprocess_image(
                image, self.height, self.width, is_training=self.is_training)

        return processed_image, label


def make_batch_from_jpeg(filenames, batch_size=80):
    with tf.name_scope('InceptionPreprocessing'):
        if isinstance(filenames, dict):
            filenames = list(filenames.keys())

        filename_queue = tf.train.string_input_producer(filenames, shuffle=False, num_epochs=1)

        key, image = tf.WholeFileReader().read(filename_queue)
        image = tf.image.decode_jpeg(image, channels=3)
        image = inception_preprocessing.preprocess_image(image, 224, 224, is_training=False)

        return tf.train.batch([key, image], batch_size=batch_size, num_threads=1,
                              allow_smaller_final_batch=True)


def make_batch(filenames, batch_size, is_training, repeat=True):
    ds = tf.data.TFRecordDataset(filenames)
    parser = ImageParser(is_training)

    ds = ds.map(parser)
    ds = ds.prefetch(batch_size)
    if repeat:
        ds = ds.repeat()

    if is_training:
        ds = ds.shuffle(buffer_size=5000, seed=42)

    ds = ds.batch(batch_size)
    ds = ds.prefetch(10)

    return ds.make_one_shot_iterator()


def make_image_patches(filenames):
    ds = tf.data.TFRecordDataset(filenames)
    parser = ImageParser(is_training=False, make_patches=True)

    ds = ds.map(parser)
    ds = ds.prefetch(10)
    return ds.make_one_shot_iterator()


def _preprocess_with_patches(image, height, width, fraction=0.7):

    if image.dtype != tf.float32:
        image = tf.image.convert_image_dtype(image, dtype=tf.float32)

    tiles = tf.expand_dims(image, 0)
    tiles = tf.image.resize_bilinear(tiles, [320, 320],
                                     align_corners=False)
    tiles = tf.tile(tiles, [4, 1, 1, 1])
    tiles = tf.image.crop_and_resize(tiles, [
        [0, 0, fraction, fraction],
        [0, 1-fraction, fraction, 1],
        [1 - fraction, 0, 1, fraction],
        [1 - fraction, 1 - fraction, 1, 1]
    ], [0, 1, 2, 3], [height, width])

    image = tf.image.central_crop(image, central_fraction=0.875)

    if height and width:
        # Resize the image to the specified height and width.
        image = tf.expand_dims(image, 0)
        image = tf.image.resize_bilinear(image, [height, width],
                                         align_corners=False)
    image = tf.concat((image, tiles), 0)

    concat = [image]
    for i in range(5):
        concat.append(tf.expand_dims(tf.image.flip_left_right(image[i]), 0))

    image = tf.concat(concat, 0)

    image = tf.subtract(image, 0.5)
    image = tf.multiply(image, 2.0)
    return image
