import os
import sys
import struct
import numpy as np
from common_utils import dataset


def get_class_representatives_v2(filename, file_header):
    classes = {}

    with dataset.read_file(filename, file_header) as f:
        raw_id = f.read(4)
        no_classes = struct.unpack('<I', raw_id)[0]
        print("Number of classes:", no_classes)
        raw_id = f.read(4)

        no_images = 800000

        dti = np.dtype(np.int32)
        dti = dti.newbyteorder('<')

        dtf = np.dtype(np.float32)
        dtf = dtf.newbyteorder('<')

        for i in range(no_classes):
            print(i, end="\r")
            classes[i] = {
                "len": 0,
                "img_ids": np.zeros([no_images], np.int32),
                "values": np.zeros([no_images], np.float32)
            }

        i = 0
        while raw_id != b'':
            i += 1
            image_id = struct.unpack('<I', raw_id)[0]
            no_indexes = struct.unpack('<I', f.read(4))[0]

            image_indices = np.frombuffer(f.read(4 * no_indexes), dtype=dti) # struct.unpack("<" + "I" * no_indexes, f.read(4 * no_indexes))
            image_values = np.frombuffer(f.read(4 * no_indexes), dtype=dtf) # struct.unpack("<" + "f" * no_indexes, f.read(4 * no_indexes))
            if i % 10000 == 0:
                print(i, end="\r")

            raw_id = f.read(4)

            for j in range(no_indexes):
                index = image_indices[j]
                val = image_values[j]

                length = classes[index]["len"]

                classes[index]["img_ids"][length] = image_id
                classes[index]["values"][length] = val

                classes[index]["len"] += 1


                # if ind not in classes:
                #     classes[ind] = [(image_id, val)]
                # else:
                #     classes[ind].append((image_id, val))
        for i in range(no_classes):
            l = classes[i]["len"]
            classes[i]["img_ids"] = classes[i]["img_ids"][:l]
            classes[i]["values"] = classes[i]["values"][:l]
            print(i, l)
    return classes


def get_class_representatives(filename, num_classes_per_image):
    classes = {}
    indices_format = '<' + 'I' * num_classes_per_image
    values_format = '<' + 'f' * num_classes_per_image

    with open(filename, 'rb') as f:
        raw_id = f.read(4)
        while raw_id != b'':
            image_id = struct.unpack('<I', raw_id)[0]
            image_indices = struct.unpack(indices_format, f.read(4 * num_classes_per_image))
            image_values = struct.unpack(values_format, f.read(4 * num_classes_per_image))
            raw_id = f.read(4)

            # annotate only videos [0,699]
            # if image_id > 47148:
            #     continue

            for ind, val in zip(image_indices, image_values):
                if ind not in classes:
                    classes[ind] = [(image_id, val)]
                else:
                    classes[ind].append((image_id, val))
    return classes


def list_annotation_files(directory):
    l = []
    d = os.listdir(directory)

    for index, video in enumerate(d):
        sys.stdout.write('\rSearching for annotations in {} ({:d}/{:d}).'.format(video, index, len(d)))
        sys.stdout.flush()
        if os.path.isdir(os.path.join(directory, video)):
            frames = os.listdir(os.path.join(directory, video))
            for frame in frames:
                if frame.endswith('.jpg.txt'):
                    l.append(os.path.join(directory, video, frame))

    sys.stdout.write('\rFound {:d} annotations.\n'.format(len(l)))
    sys.stdout.flush()
    return l


def read_annotation_file(file, max_no=None, max_prob=None):
    l = []
    with open(file, 'r') as f:
        for index, line in enumerate(f):
            if line == '':
                continue;

            parts = line.split(';')
            prob = float(parts[1])

            if max_prob and prob < max_prob:
                continue

            l.append((parts[0], prob))
    l.sort(key=lambda t: -t[1])
    if max_no and max_no < len(l):
        l = l[:max_no]
    return l


def filename_to_id(file):
    file = os.path.split(file)[-1].split('_')
    video_id = (int(file[0][1:]) - 35345) << 18
    frame = int(file[1][1:])
    return video_id + frame


#print(read_annotation_file('c:\\Users\\Tom\\Workspace\\KeywordSearch\\tensorflow\\bin\\annotation\\39745\\v39745_f00001_s0000_0000.03sec.jpg.txt', max_prob=1))