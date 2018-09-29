import pickle
import tensorflow as tf


class Model:

    def __init__(self, weight_file_path):
        with open(weight_file_path, "rb") as f:
            self.mat_blocks_dict, self.mat_params_dict = pickle.load(f)

    def get_weights(self, key):
        assert key in self.mat_params_dict, "key: " + key + " not found."
        return self.mat_params_dict[key]

    def get_initializer(self, key):
        return tf.constant_initializer(self.get_weights(key), dtype=tf.float32)

    def batch_norm(self, inputs, name, epsilon=1.0e-5):
        name2 = "bn" + name[3:]
        if name.startswith("conv"):
            name2 = "bn_" + name

        scale = self.get_initializer(name2 + '_scale')
        offset = self.get_initializer(name2 + '_offset')
        mean = self.get_initializer(name2 + '_mean')
        variance = self.get_initializer(name2 + '_variance')

        return tf.layers.batch_normalization(inputs, beta_initializer=offset, gamma_initializer=scale,
                                             moving_mean_initializer=mean, moving_variance_initializer=variance,
                                             epsilon=epsilon)

    def conv2d(self, inputs, name, filters, kernel_size, strides=(1, 1), padding="SAME", use_bias=False,
                   add_relu=True, add_bn=True):
        weights = self.get_initializer(name + '_filter')
        bias = self.get_initializer(name + "_bias") if use_bias else None

        conv = tf.layers.conv2d(inputs, filters, kernel_size, strides=strides, padding=padding, use_bias=use_bias,
                                kernel_initializer=weights, bias_initializer=bias)
        if add_bn:
            conv = self.batch_norm(conv, name)
        if add_relu:
            conv = tf.nn.relu(conv)
        return conv

    def conv2d_transpose(self, inputs, name, filters, kernel_size, strides=(1, 1), padding="SAME", use_bias=False):
        weights = self.get_initializer(name + '_filter')
        bias = self.get_initializer(name + "_bias") if use_bias else None

        conv = tf.layers.conv2d_transpose(inputs, filters, kernel_size, strides=strides, padding=padding,
                                          use_bias=use_bias, kernel_initializer=weights, bias_initializer=bias)
        return conv

    def conv_trans_layer(self, inputs, name, shape, strides=[1, 1, 1, 1], padding="SAME", use_bias=False):
        weights = self.get_initializer(name + '_filter')
        weights = tf.get_variable(name + "_filter", shape, initializer=weights, dtype=tf.float32)

        nb, h, w, nc = tf.split(tf.shape(inputs), num_or_size_splits=4)
        out_shape = tf.stack([nb, (h - 1) * strides[1] - 3 + shape[0], (w - 1) * strides[2] - 3 + shape[1], nc])[:, 0]
        conv = tf.nn.conv2d_transpose(inputs, weights, out_shape, strides, padding=padding)

        if use_bias:
            bias = self.get_initializer(name + "_bias")
            bias = tf.get_variable(name + "_bias", shape, initializer=bias, dtype=tf.float32)
            conv = tf.nn.bias_add(conv, bias)
        return conv

    def residual_block(self, inputs, name, neck_channel, out_channel, trunk):
        strides = (2, 2) if name.startswith("res3a") or name.startswith("res4a") else (1, 1)

        res = self.conv2d(inputs, name + '_branch2a', filters=neck_channel, kernel_size=1, strides=strides,
                        padding="VALID", add_relu=True)
        res = self.conv2d(res, name + '_branch2b', filters=neck_channel, kernel_size=3, padding="SAME", add_relu=True)
        res = self.conv2d(res, name + '_branch2c', filters=out_channel, kernel_size=1, padding="VALID", add_relu=False)

        res = trunk + res
        return tf.nn.relu(res)

    def tiny_face(self, image):
        img = tf.pad(image, [[0, 0], [3, 3], [3, 3], [0, 0]], "CONSTANT")
        conv = self.conv2d(img, "conv1", filters=64, kernel_size=7, strides=2, padding="VALID", add_relu=True)
        pool1 = tf.layers.max_pooling2d(conv, pool_size=3, strides=2, padding='SAME')

        res2a_branch1 = self.conv2d(pool1, 'res2a_branch1', filters=256, kernel_size=1, padding="VALID", add_relu=False)
        res2a = self.residual_block(pool1, 'res2a', 64, 256, res2a_branch1)
        res2b = self.residual_block(res2a, 'res2b', 64, 256, res2a)
        res2c = self.residual_block(res2b, 'res2c', 64, 256, res2b)

        res3a_branch1 = self.conv2d(res2c, 'res3a_branch1', filters=512, kernel_size=1, strides=2, padding="VALID",
                                    add_relu=False)
        res3a = self.residual_block(res2c, 'res3a', 128, 512, res3a_branch1)

        res3b1 = self.residual_block(res3a, 'res3b1', 128, 512, res3a)
        res3b2 = self.residual_block(res3b1, 'res3b2', 128, 512, res3b1)
        res3b3 = self.residual_block(res3b2, 'res3b3', 128, 512, res3b2)

        res4a_branch1 = self.conv2d(res3b3, 'res4a_branch1', filters=1024, kernel_size=1, strides=2, padding="VALID",
                                    add_relu=False)
        res4a = self.residual_block(res3b3, 'res4a', 256, 1024, res4a_branch1)

        res4b = res4a
        for i in range(1, 23):
            res4b = self.residual_block(res4b, 'res4b' + str(i), 256, 1024, res4b)

        score_res4 = self.conv2d(res4b, 'score_res4', filters=125, kernel_size=1, padding="VALID", use_bias=True,
                                 add_relu=False, add_bn=False)
        score4 = self.conv_trans_layer(score_res4, 'score4', shape=[4, 4, 125, 125], strides=[1, 2, 2, 1],
                                       padding="SAME")
        # score4 = self.conv2d_transpose(score_res4, 'score4', filters=125, kernel_size=4, strides=2, padding="SAME")
        score_res3 = self.conv2d(res3b3, 'score_res3', filters=125, kernel_size=1, padding="VALID", use_bias=True,
                                 add_bn=False, add_relu=False)

        score4_shape = tf.shape(score4)
        score_res3c = tf.image.extract_glimpse(score_res3, size=score4_shape[1:3],
                                               offsets=tf.zeros([score4_shape[0], 2]), centered=True, normalized=False)

        score_final = score4 + score_res3c
        return score_final
