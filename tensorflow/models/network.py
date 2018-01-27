import tensorflow as tf
from dataset import dataset_utils
from models import inception_v1, inception_utils, inception_preprocessing

slim = tf.contrib.slim


def build_net(inputs, num_classes, scope, is_training=True, dropout_keep_prob=0.8, base_scope='InceptionV1'):
    """Defines the Inception V1 architecture.

    Args:
      inputs: a tensor of size [batch_size, height, width, channels].
      num_classes: number of predicted classes.
      is_training: whether is actions or not.
      dropout_keep_prob: the percentage of activation values that are retained.
      scope: Optional variable_scope.

    Returns:
      logits: the pre-softmax activations, a tensor of size
        [batch_size, num_classes]
      end_points: a dictionary from components of the models to the corresponding
        activation.
    """

    with slim.arg_scope([slim.batch_norm, slim.dropout], is_training=is_training):
        with slim.arg_scope(inception_utils.inception_arg_scope()):
            net, end_points = inception_v1.inception_v1_base(inputs, scope=base_scope)

        with tf.variable_scope(scope, reuse=False):
            net = slim.avg_pool2d(net, [7, 7], stride=1, scope='AvgPool_0a_7x7')
            end_points['AvgPool_0a_7x7'] = net

            net = slim.dropout(net, dropout_keep_prob, scope='Dropout_0b')
            logits = slim.conv2d(net, num_classes, [1, 1], activation_fn=None, normalizer_fn=None,
                                 scope='Conv2d_0c_1x1')
            logits = tf.squeeze(logits, [1, 2], name='SpatialSqueeze')

    return logits, end_points


def get_batch(tfrecord_dir, dataset_name, batch_size, image_size, is_training):
    with tf.name_scope('InceptionPreprocessing'):
        records = dataset_utils.get_tfrecord_files(tfrecord_dir, dataset_name)

        filename_queue = tf.train.string_input_producer(records, seed=42, shuffle=is_training,
                                                        num_epochs=None if is_training else 1)
        image, label = dataset_utils.get_dataset(filename_queue)

        processed_image = inception_preprocessing.preprocess_image(image, image_size, image_size,
                                                                   is_training=is_training)

        if is_training:
            return tf.train.shuffle_batch([processed_image, label], batch_size=batch_size, seed=42,
                                          capacity=10*batch_size, min_after_dequeue=8*batch_size)
        return tf.train.batch([processed_image, label], batch_size=batch_size, num_threads=1,
                              allow_smaller_final_batch=True)


def get_image_as_batch(filenames, image_size):
    with tf.name_scope('InceptionPreprocessing'):
        if isinstance(filenames, dict):
            filenames = list(filenames.keys())

        filename_queue = tf.train.string_input_producer(filenames, shuffle=False, num_epochs=1)

        key, image = tf.WholeFileReader().read(filename_queue)

        image = tf.image.decode_jpeg(image, channels=3)

        image = inception_preprocessing.preprocess_image(image, image_size, image_size, is_training=False)
        # return key, tf.expand_dims(image, 0)
        return tf.train.batch([key, image], batch_size=80, num_threads=1,
                              allow_smaller_final_batch=True)
