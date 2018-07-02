import struct
import argparse
import numpy as np

from common_utils import dataset, console
from common_utils.dataset import DEFAULT_HEADER
HEADER = DEFAULT_HEADER


def create_index_file(pseudo_index_filename, index_filename):
    classes = get_class_representatives(pseudo_index_filename)

    pt = console.ProgressTracker()
    pt.info(">> Creating inverted index...")
    pt.reset(len(classes))

    file = open(index_filename, "wb")

    file.write(b'KS INDEX')
    file.write(b'\xff\xff\xff\xff\xff\xff\xff\xff')

    offset = len(classes) * 8 + 16 + 8
    sorted_classes = sorted(classes)

    for key in sorted_classes:
        file.write(struct.pack("I", key) + struct.pack("I", offset))
        offset += classes[key]["len"] * 8 + 8
    file.write(b'\xff\xff\xff\xff\xff\xff\xff\xff')

    for key in sorted_classes:
        photos = list(zip(classes[key]["img_ids"], classes[key]["values"]))
        photos.sort(key=lambda tup: -tup[1])
        for photo_id, photo_val in photos:
            file.write(struct.pack("I", photo_id) + struct.pack("f", photo_val))
        file.write(b'\xff\xff\xff\xff\xff\xff\xff\xff')
        pt.increment()

    file.close()
    pt.info(">> Inverted index created.")


def get_class_representatives(filename, max_images_per_class=800000):
    classes = {}
    pt = console.ProgressTracker()

    with dataset.read_file(filename, HEADER) as f:
        raw_id = f.read(4)
        no_classes = struct.unpack("<I", raw_id)[0]
        raw_id = f.read(4)

        dti = np.dtype(np.int32).newbyteorder("<")
        dtf = np.dtype(np.float32).newbyteorder("<")

        pt.info(">> Creating class representatives...")
        pt.reset(no_classes)
        for i in range(no_classes):
            classes[i] = {
                "len": 0,
                "img_ids": np.zeros([max_images_per_class], np.int32),
                "values": np.zeros([max_images_per_class], np.float32)
            }
            pt.increment()

        pt.info(">> Reading image classes...")
        i = 0
        while raw_id != b'':
            i += 1
            image_id = struct.unpack("<I", raw_id)[0]
            no_indexes = struct.unpack("<I", f.read(4))[0]

            image_indices = np.frombuffer(f.read(4 * no_indexes), dtype=dti)
            image_values = np.frombuffer(f.read(4 * no_indexes), dtype=dtf)
            if i % 10000 == 0:
                pt.progress_info("\t> Images read: {}", [i])

            raw_id = f.read(4)

            for j in range(no_indexes):
                index = image_indices[j]
                val = image_values[j]

                length = classes[index]["len"]

                classes[index]["img_ids"][length] = image_id
                classes[index]["values"][length] = val

                classes[index]["len"] += 1

        for i in range(no_classes):
            l = classes[i]["len"]
            classes[i]["img_ids"] = classes[i]["img_ids"][:l]
            classes[i]["values"] = classes[i]["values"][:l]
    return classes


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pseudo_index_filename', help='location of pseudo-index file')
    parser.add_argument('--index_filename', help='name of the new index file')
    args = parser.parse_args()

    create_index_file(args.pseudo_index_filename, args.index_filename)
