import os
import struct
import numpy as np


def store_vector(vector, file, text_dtype):
    frmt = '<'+text_dtype*len(vector)
    with open(file, 'wb') as f:
        f.write(struct.pack('<I', len(vector)))
        f.write(struct.pack(frmt, *vector))


def store_matrix(matrix, file, text_dtype):
    frmt = '<' + text_dtype * len(matrix[0])
    with open(file, 'wb') as f:
        f.write(struct.pack('<I', len(matrix[0])))
        for i in range(len(matrix)):
            f.write(struct.pack(frmt, *matrix[i]))


def read_matrix(file, text_dtype, dtype):
    with open(file, 'rb') as f:
        dimensions = struct.unpack('<I', f.read(4))[0]
        frmt = '<'+text_dtype*dimensions

        matrix = np.zeros((dimensions, dimensions), dtype=dtype)

        for i in range(dimensions):
            dt = np.dtype(dtype).newbyteorder('<')
            matrix[i] = np.frombuffer(f.read(dimensions*4), dtype=dt)
    return dimensions, matrix


def store_covariance_matrix(mean, cov, no_images, folder, dataset_name):
    store_vector(mean, os.path.join(folder, 'mean_unorm-{}.bin'.format(dataset_name)), 'f')
    store_matrix(cov, os.path.join(folder, 'covariance_unorm-{}.bin'.format(dataset_name)), 'f')

    # E[XX^T]-E[X]E[X]^T
    mean = mean / no_images
    cov = cov / no_images - np.outer(mean, mean)

    store_vector(mean, os.path.join(folder, 'mean-{}.bin'.format(dataset_name)), 'f')
    store_matrix(cov, os.path.join(folder, 'covariance-{}.bin'.format(dataset_name)), 'f')


def store_confusion_matrix(matrix, folder, dataset_name):
    store_matrix(matrix, os.path.join(folder, 'confusion-{}.bin'.format(dataset_name)), 'I')
