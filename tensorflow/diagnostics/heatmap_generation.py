# https://stackoverflow.com/questions/2374959/algorithm-to-convert-any-positive-integer-to-an-rgb-value
import os
import sys
import struct
import numpy as np
from PIL import Image
from diagnostics import heatmap_utils


def create_heatmap(dimensions, matrix):
    img = Image.new('RGB', (dimensions, dimensions))

    for i in range(dimensions):
        sys.stdout.write('\r>> Generating row {:d}/{:d}'.format(i, dimensions))
        sys.stdout.flush()
        for j in range(dimensions):
            img.putpixel((i, j), value_to_color(matrix[i][j]))

    sys.stdout.write('\rImage generated.\n')
    sys.stdout.flush()
    return img


def matrix_to_png(folder, filename, text_dtype, dtype, power):
    dimensions, matrix = heatmap_utils.read_matrix(os.path.join(folder, '{}.bin'.format(filename)), text_dtype, dtype)

    min_val, max_val = matrix.min(), matrix.max()
    print("Max: ", str(max_val), "\nMin: ", str(min_val))

    matrix = np.log10((matrix - min_val) / (max_val - min_val) * 9 + 1)
    #matrix = np.power((matrix - min_val)/(max_val-min_val), power)

    min_val, max_val = matrix.min(), matrix.max()
    print("Normalized max: ", str(max_val), "\nNormalized min: ", str(min_val))

    img = create_heatmap(dimensions, matrix)
    img.save(os.path.join(folder, '{}.png'.format(filename)))


def value_to_color(val):
    if val < 0:
        return 255, 255, 255
    if val > 1:
        return 0, 0, 0

    r, g, b = 0, 0, 0
    if val < 0.125:
        b = round(127 + 128 * val / 0.125)
        g = 0
        r = 0
    elif val < 0.375:
        b = 255
        g = round(((val - 0.125) / 0.25) * 255)
        r = 0
    elif val < 0.625:
        b = round((1 - (val - 0.375) / 0.25) * 255)
        g = 255
        r = round(((val - 0.375) / 0.25) * 255)
    elif val < 0.875:
        b = 0
        g = round((1 - (val - 0.625) / 0.25) * 255)
        r = 255
    else:
        b = 0
        g = 0
        r = round(255 - 128 * (val - 0.875) / 0.125)

    return int(r), int(g), int(b)


def print_color_scale():
    img = Image.new('RGB', (201, 20))

    i = 0
    while i <= 200:
        c = value_to_color(i/200)
        for a in range(20):
            img.putpixel((i, a), c)
        i += 1

    img.save('bin/covariance/scale.png')

#matrix_to_png('bin/covariance', 'covariance-classification', 'f', np.float32, 1/3)
matrix_to_png('bin/covariance', 'covariance-train1390', 'f', np.float32, 1/4)
matrix_to_png('bin/covariance', 'confusion-train1390', 'I', np.int32, 1)
