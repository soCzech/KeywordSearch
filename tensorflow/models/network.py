import tensorflow as tf
from models import inception_v1, inception_utils
from models import nasnet, nasnet_utils

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


def build_nasnet(inputs, num_classes, is_training=True, use_large=False):
    data_format = 'NHWC'

    num_cells = 12
    drop_path_keep_prob = 1.0
    total_training_steps = 250000  # matters only if drop_path_keep_prob < 1.0
    num_conv_filters = 44
    dense_dropout_keep_prob = 0.5
    filter_scaling_rate = 2.0
    num_reduction_layers = 2
    skip_reduction_layer_input = 0
    stem_multiplier = 1.0

    if use_large:
        num_cells = 18
        num_conv_filters = 168
        drop_path_keep_prob = 0.7
        skip_reduction_layer_input = 1
        stem_multiplier = 3.0

    if not is_training:
        drop_path_keep_prob = 1.0

    arg_scope = nasnet.nasnet_mobile_arg_scope()
    with slim.arg_scope(arg_scope):
        if tf.test.is_gpu_available() and data_format == 'NHWC':
            tf.logging.info('A GPU is available on the machine, consider using NCHW '
                            'data format for increased speed on GPU.')

        if data_format == 'NCHW':
            inputs = tf.transpose(inputs, [0, 3, 1, 2])

        # Calculate the total number of cells in the network
        # Add 2 for the reduction cells
        total_num_cells = num_cells + 2
        # If ImageNet, then add an additional two for the stem cells
        total_num_cells += 2

        normal_cell = nasnet_utils.NasNetANormalCell(
            num_conv_filters, drop_path_keep_prob,
            total_num_cells, total_training_steps)
        reduction_cell = nasnet_utils.NasNetAReductionCell(
            num_conv_filters, drop_path_keep_prob,
            total_num_cells, total_training_steps)

        with tf.contrib.framework.arg_scope([slim.dropout, nasnet_utils.drop_path, slim.batch_norm],
                                            is_training=is_training):
            with tf.contrib.framework.arg_scope([slim.avg_pool2d, slim.max_pool2d, slim.conv2d, slim.batch_norm,
                                                 slim.separable_conv2d, nasnet_utils.factorized_reduction,
                                                 nasnet_utils.global_avg_pool, nasnet_utils.get_channel_index,
                                                 nasnet_utils.get_channel_dim], data_format=data_format):
                net, end_points = nasnet._build_nasnet_base(inputs,
                                                            normal_cell=normal_cell,
                                                            reduction_cell=reduction_cell,
                                                            num_cells=num_cells,
                                                            num_reduction_layers=num_reduction_layers,
                                                            skip_reduction_layer_input=skip_reduction_layer_input,
                                                            filter_scaling_rate=filter_scaling_rate,
                                                            stem_multiplier=stem_multiplier,
                                                            final_endpoint=None,
                                                            current_step=None)

                # Final softmax layer
                with tf.variable_scope('final_layer'):
                    net = tf.nn.relu(net)
                    net = nasnet_utils.global_avg_pool(net)
                    end_points["DeepFeatures"] = net
                    net = slim.dropout(net, dense_dropout_keep_prob, scope='dropout')
                    logits = slim.fully_connected(net, num_classes)
                return logits, end_points


# def build_nasnet_large(inputs, num_classes, is_training=True):
#     data_format = 'NHWC'
#     num_cells = 18
#     num_conv_filters = 168
#     drop_path_keep_prob = 1.0
#     total_training_steps = 0  # matters only if drop_path_keep_prob < 1.0
#     num_reduction_layers = 2
#     filter_scaling_rate = 2.0
#     skip_reduction_layer_input = 1
#     dense_dropout_keep_prob = 0.5
#     stem_multiplier = 3.0
#
#     if not is_training:
#         drop_path_keep_prob = 1.0
#
#     arg_scope = nasnet.nasnet_mobile_arg_scope()
#     with slim.arg_scope(arg_scope):
#         if tf.test.is_gpu_available() and data_format == 'NHWC':
#             tf.logging.info('A GPU is available on the machine, consider using NCHW '
#                             'data format for increased speed on GPU.')
#
#         if data_format == 'NCHW':
#             inputs = tf.transpose(inputs, [0, 3, 1, 2])
#
#         # Calculate the total number of cells in the network
#         # Add 2 for the reduction cells
#         total_num_cells = num_cells + 2
#         # If ImageNet, then add an additional two for the stem cells
#         total_num_cells += 2
#
#         normal_cell = nasnet_utils.NasNetANormalCell(
#             num_conv_filters, drop_path_keep_prob,
#             total_num_cells, total_training_steps)
#         reduction_cell = nasnet_utils.NasNetAReductionCell(
#             num_conv_filters, drop_path_keep_prob,
#             total_num_cells, total_training_steps)
#
#         with tf.contrib.framework.arg_scope([slim.dropout, nasnet_utils.drop_path, slim.batch_norm],
#                                             is_training=is_training):
#             with tf.contrib.framework.arg_scope([slim.avg_pool2d, slim.max_pool2d, slim.conv2d, slim.batch_norm,
#                                                  slim.separable_conv2d, nasnet_utils.factorized_reduction,
#                                                  nasnet_utils.global_avg_pool, nasnet_utils.get_channel_index,
#                                                  nasnet_utils.get_channel_dim], data_format=data_format):
#                 net, end_points = nasnet._build_nasnet_base(inputs,
#                                                  normal_cell=normal_cell,
#                                                  reduction_cell=reduction_cell,
#                                                  num_cells=num_cells,
#                                                  num_reduction_layers=num_reduction_layers,
#                                                  skip_reduction_layer_input=skip_reduction_layer_input,
#                                                  filter_scaling_rate=filter_scaling_rate,
#                                                  stem_multiplier=stem_multiplier,
#                                                  final_endpoint=None,
#                                                  current_step=None)
#
#                 # Final softmax layer
#                 with tf.variable_scope('final_layer'):
#                     net = tf.nn.relu(net)
#                     net = nasnet_utils.global_avg_pool(net)
#                     net = slim.dropout(net, dense_dropout_keep_prob, scope='dropout')
#                     logits = slim.fully_connected(net, num_classes)
#                 return logits, end_points
