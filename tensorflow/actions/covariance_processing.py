# https://stackoverflow.com/questions/2374959/algorithm-to-convert-any-positive-integer-to-an-rgb-value
import os
import struct
import numpy as np
from PIL import Image


def covariance_matrix_to_png(folder, filename):
    with open(os.path.join(folder, filename), 'rb') as f:
        dimensions = struct.unpack('<I', f.read(4))[0]
        frmt = '<'+'f'*dimensions

        matrix = np.zeros((dimensions, dimensions), dtype=np.float32)

        for i in range(dimensions):
            dt = np.dtype(np.float32).newbyteorder('<')
            matrix[i] = np.frombuffer(f.read(dimensions*4), dtype=dt)

    max_val = matrix.max()
    print("Max: " + max_val)

    img = Image.new((dimensions, dimensions))

    for i in range(dimensions):
        for j in range(dimensions):
            img.putpixel((i, j), value_to_color(matrix[i][j]))

    img.save(os.path.join(folder, 'covariance.png'))


def value_to_color(val):
    r, g, b = 0, 0, 0
    if val < 0.125:
        b = round(127 + 128 * val / 0.125)
    elif val < 0.375:
        b = 255
    elif val < 0.625:
        b = round((1 - (val - 0.375) / 0.25) * 255)
    else:
        b = 0

    if val < 0.125:
        g = 0
    elif val < 0.375:
        g = round(((val - 0.125) / 0.25) * 255)
    elif val < 0.625:
        g = 255
    elif val < 0.875:
        g = round((1 - (val - 0.625) / 0.25) * 255)
    else:
        g = 0

    if val < 0.375:
        r = 0
    elif val < 0.625:
        r = round(((val - 0.375) / 0.25) * 255)
    elif val < 0.875:
        r = 255
    else:
        r = round(255 - 128 * (val - 0.875) / 0.125)
    return r, g, b


def print_color_scale():
    img = Image.new('RGB', (201, 20))

    i = 0
    while i <= 200:
        c=value_to_color(i/200)
        for a in range(20):
            img.putpixel((i, a), c)
        i += 1

    img.save('bin/covariance/scale.png')


covariance_matrix_to_png('bin/covariance', 'covariance.bin')