# Copyright 2017 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Contains the definition for the NASNet classification networks.

Paper: https://arxiv.org/abs/1707.07012
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf

from models import nasnet_utils

arg_scope = tf.contrib.framework.arg_scope
slim = tf.contrib.slim


# Notes for training the mobile NASNet ImageNet model
# -------------------------------------
# batch size (per replica): 32
# learning rate: 0.04 * 50
# learning rate scaling factor: 0.97
# num epochs per decay: 2.4
# sync sgd with 50 replicas
# auxiliary head weighting: 0.4
# label smoothing: 0.1
# clip global norm of all gradients by 10
def mobile_imagenet_config():
  return tf.contrib.training.HParams(
      stem_multiplier=1.0,
      dense_dropout_keep_prob=0.5,
      num_cells=12,
      filter_scaling_rate=2.0,
      drop_path_keep_prob=1.0,
      num_conv_filters=44,
      use_aux_head=1,
      num_reduction_layers=2,
      data_format='NHWC',
      skip_reduction_layer_input=0,
      total_training_steps=250000,
  )


def nasnet_mobile_arg_scope(weight_decay=4e-5,
                            batch_norm_decay=0.9997,
                            batch_norm_epsilon=1e-3):
  """Defines the default arg scope for the NASNet-A Mobile ImageNet model.

  Args:
    weight_decay: The weight decay to use for regularizing the model.
    batch_norm_decay: Decay for batch norm moving average.
    batch_norm_epsilon: Small float added to variance to avoid dividing by zero
      in batch norm.

  Returns:
    An `arg_scope` to use for the NASNet Mobile Model.
  """
  batch_norm_params = {
      # Decay for the moving averages.
      'decay': batch_norm_decay,
      # epsilon to prevent 0s in variance.
      'epsilon': batch_norm_epsilon,
      'scale': True,
      'fused': True,
  }
  weights_regularizer = tf.contrib.layers.l2_regularizer(weight_decay)
  weights_initializer = tf.contrib.layers.variance_scaling_initializer(
      mode='FAN_OUT')
  with arg_scope([slim.fully_connected, slim.conv2d, slim.separable_conv2d],
                 weights_regularizer=weights_regularizer,
                 weights_initializer=weights_initializer):
    with arg_scope([slim.fully_connected],
                   activation_fn=None, scope='FC'):
      with arg_scope([slim.conv2d, slim.separable_conv2d],
                     activation_fn=None, biases_initializer=None):
        with arg_scope([slim.batch_norm], **batch_norm_params) as sc:
          return sc


def _imagenet_stem(inputs, filter_scaling_rate, stem_cell, current_step=None):
  """Stem used for models trained on ImageNet."""
  num_stem_cells = 2
  stem_multiplier = 1.0

  # 149 x 149 x 32
  num_stem_filters = int(32 * stem_multiplier)
  net = slim.conv2d(
      inputs, num_stem_filters, [3, 3], stride=2, scope='conv0',
      padding='VALID')
  net = slim.batch_norm(net, scope='conv0_bn')

  # Run the reduction cells
  cell_outputs = [None, net]
  filter_scaling = 1.0 / (filter_scaling_rate**num_stem_cells)
  for cell_num in range(num_stem_cells):
    net = stem_cell(
        net,
        scope='cell_stem_{}'.format(cell_num),
        filter_scaling=filter_scaling,
        stride=2,
        prev_layer=cell_outputs[-2],
        cell_num=cell_num,
        current_step=current_step)
    cell_outputs.append(net)
    filter_scaling *= filter_scaling_rate
  return net, cell_outputs


# build_nasnet_mobile.default_image_size = 224


def _build_nasnet_base(images,
                       normal_cell,
                       reduction_cell,
                       num_cells,
                       num_reduction_layers,
                       skip_reduction_layer_input,
                       filter_scaling_rate,
                       final_endpoint=None,
                       current_step=None):
  """Constructs a NASNet image model."""

  end_points = {}
  def add_and_check_endpoint(endpoint_name, net):
    end_points[endpoint_name] = net
    return final_endpoint and (endpoint_name == final_endpoint)

  # Find where to place the reduction cells or stride normal cells
  reduction_indices = nasnet_utils.calc_reduction_layers(
      num_cells, num_reduction_layers)
  stem_cell = reduction_cell

  net, cell_outputs = _imagenet_stem(images, filter_scaling_rate, stem_cell)
  if add_and_check_endpoint('Stem', net): return net, end_points

  # Setup for building in the auxiliary head.
  aux_head_cell_idxes = []
  if len(reduction_indices) >= 2:
    aux_head_cell_idxes.append(reduction_indices[1] - 1)

  # Run the cells
  filter_scaling = 1.0
  # true_cell_num accounts for the stem cells
  true_cell_num = 2
  for cell_num in range(num_cells):
    stride = 1
    if skip_reduction_layer_input:
      prev_layer = cell_outputs[-2]
    if cell_num in reduction_indices:
      filter_scaling *= filter_scaling_rate
      net = reduction_cell(
          net,
          scope='reduction_cell_{}'.format(reduction_indices.index(cell_num)),
          filter_scaling=filter_scaling,
          stride=2,
          prev_layer=cell_outputs[-2],
          cell_num=true_cell_num,
          current_step=current_step)
      if add_and_check_endpoint(
          'Reduction_Cell_{}'.format(reduction_indices.index(cell_num)), net):
        return net, end_points
      true_cell_num += 1
      cell_outputs.append(net)
    if not skip_reduction_layer_input:
      prev_layer = cell_outputs[-2]
    net = normal_cell(
        net,
        scope='cell_{}'.format(cell_num),
        filter_scaling=filter_scaling,
        stride=stride,
        prev_layer=prev_layer,
        cell_num=true_cell_num,
        current_step=current_step)

    if add_and_check_endpoint('Cell_{}'.format(cell_num), net):
      return net, end_points
    true_cell_num += 1
    cell_outputs.append(net)

  return net, end_points
