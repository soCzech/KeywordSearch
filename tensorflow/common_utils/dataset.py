import os
import struct
import numpy as np

from common_utils import console

BACHELOR_THESIS_HEADER = [b'BC\0\0\0\0\0\0\0\0\0\0\0\0\0\0', b'2018-04-01 00:00:00\n']
VBS2018_HEADER = [b'TRECVid\0\0\0\0\0\0\0\0\0', b'2018-01-26 10:00:00\n']

DEFAULT_HEADER = [b'V3C1-FIRST750\0\0\0', b'2018-11-11 00:00:00\n']


def create_file(path, struct_data_list, file_header):
    """Creates a file with a given header.

    Args:
        path: Path and name where to create the file.
        struct_data_list: List of (data_format, data) to write to the file after the header using struct.pack().
        file_header: File header as a list of byte strings.

    Returns:
        Handle of the created file.
    """
    file = open(path, 'wb')
    for line in file_header:
        file.write(line)

    for data_format, data in struct_data_list:
        file.write(struct.pack(data_format, data))

    return file


def read_file(path, file_header):
    """Reads a file with a given name and header.

    Args:
        path: Path and name of a file to read.
        file_header: File header as a list of byte strings.

    Returns:
        Handle to start of the file's content after the header. Or exception if headers do not match.
    """
    file = open(path, 'rb')
    for line in file_header:
        assert file.read(len(line)) == line, "File header mismatch!"

    return file


def read_deep_features(path):
    """Reads deep features file.

    Args:
        path: Path to a file to read.

    Returns:
        Dictionary of tuples (id, numpy array).
    """
    d = dict()
    file = read_file(path, DEFAULT_HEADER)
    df_shape = struct.unpack('<I', file.read(4))[0]

    byte_id = file.read(4)

    while byte_id != b'':
        file_id = struct.unpack('<I', byte_id)[0]
        if file_id not in d:
            d[file_id] = []
        d[file_id].append(np.frombuffer(file.read(df_shape * 4), dtype=np.float32))

        byte_id = file.read(4)

    return d


def get_images_from_disk(directory):
    """Reads files in folder.

    Args:
        directory: Folder to read from.

    Returns:
        Dictionary of tuples (file_absolute_path, id).
    """
    directory = os.path.normpath(directory)
    image_id = 0
    res = dict()

    sorted_list = sorted(os.listdir(directory))
    pt = console.ProgressTracker()
    pt.info(">> Reading image files...")
    pt.reset(len(sorted_list))

    for folder in sorted_list:
        if os.path.isdir(os.path.join(directory, folder)):
            for image in sorted(os.listdir(os.path.join(directory, folder))):
                res[os.path.join(directory, folder, image)] = image_id
                image_id += 1
        pt.increment()
    return res
