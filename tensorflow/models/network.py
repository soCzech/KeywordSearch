import tensorflow as tf
from models import inception_v1, inception_utils

slim = tf.contrib.slim


def build_net(inputs, num_classes, is_training=True, dropout_keep_prob=0.8, base_scope='InceptionV1'):
    """Defines the Inception V1 architecture.

    Args:
      inputs: a tensor of size [batch_size, height, width, channels].
      num_classes: number of predicted classes.
      is_training: whether is actions or not.
      dropout_keep_prob: the percentage of activation values that are retained.
      base_scope: Optional variable_scope.

    Returns:
      logits: the pre-softmax activations, a tensor of size
        [batch_size, num_classes]
      end_points: a dictionary from components of the models to the corresponding
        activation.
    """

    with slim.arg_scope([slim.batch_norm, slim.dropout], is_training=is_training):
        with slim.arg_scope(inception_utils.inception_arg_scope()):
            net, end_points = inception_v1.inception_v1_base(inputs, scope=base_scope)

        with tf.variable_scope('Logits'):
            net = slim.avg_pool2d(net, [7, 7], stride=1, scope='AvgPool_0a_7x7')
            end_points['AvgPool_0a_7x7'] = net

            net = slim.dropout(net, dropout_keep_prob, scope='Dropout_0b')
            logits = slim.conv2d(net, num_classes, [1, 1], activation_fn=None, normalizer_fn=None,
                                 scope='Conv2d_0c_1x1')
            logits = tf.squeeze(logits, [1, 2], name='SpatialSqueeze')

    return logits, end_points
