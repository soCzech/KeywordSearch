import struct
import numpy as np

BACHELOR_THESIS_HEADER = [b'TomasSoucek\0\0\0\0\0', b'2018-04-01 00:00:00\n']
VBS2018_HEADER = [b'TRECVid\0\0\0\0\0\0\0\0\0', b'2018-01-26 10:00:00\n']
DEFAULT_HEADER = VBS2018_HEADER


def create_file(path, struct_data_list, file_header):
    file = open(path, 'wb')
    for line in file_header:
        file.write(line)

    for data_format, data in struct_data_list:
        file.write(struct.pack(data_format, data))

    return file


def read_file(path, file_header):
    file = open(path, 'rb')
    for line in file_header:
        assert file.read(len(line)) == line, "File header mismatch!"

    return file


def read_deep_features(path):
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
