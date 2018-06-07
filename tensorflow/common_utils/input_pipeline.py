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

    def __init__(self, is_training):
        self.is_training = is_training
        self.width = 224
        self.height = 224

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
        processed_image = inception_preprocessing.preprocess_image(
            image, self.height, self.width, is_training=self.is_training)

        return processed_image, label


def make_batch(filenames, batch_size, is_training):
    ds = tf.data.TFRecordDataset(filenames)
    parser = ImageParser(is_training)

    ds = ds.map(parser)
    ds = ds.prefetch(batch_size)
    ds = ds.repeat()

    if is_training:
        ds = ds.shuffle(buffer_size=5000, seed=42)

    ds = ds.batch(batch_size)
    ds = ds.prefetch(10)

    return ds.make_one_shot_iterator()
