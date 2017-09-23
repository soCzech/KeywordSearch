from deployment import index_utils
import struct
import argparse


def create_index_file(pseudo_index_filename, index_filename, num_classes_per_image):
    classes = index_utils.get_class_representatives(pseudo_index_filename, num_classes_per_image)
    file = open(index_filename, 'wb')

    file.write(b'KS INDEX')
    file.write(b'\xff\xff\xff\xff\xff\xff\xff\xff')

    offset = len(classes) * 8 + 16 + 8
    sorted_classes = sorted(classes)

    for key in sorted_classes:
        file.write(struct.pack('I', key) + struct.pack('I', offset))
        offset += len(classes[key]) * 8 + 8
    file.write(b'\xff\xff\xff\xff\xff\xff\xff\xff')

    for key in sorted_classes:
        photos = classes[key]
        photos.sort(key=lambda tup: -tup[1])
        for photo_id, photo_val in photos:
            file.write(struct.pack('I', photo_id) + struct.pack('f', photo_val))
        file.write(b'\xff\xff\xff\xff\xff\xff\xff\xff')

    file.close()

# py actions/create_index.py --pseudo_index_filename="files.pseudo-index" --index_filename="files.index" --num_classes=2
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pseudo_index_filename', required=True,
                        help='location of .pseudo-index file')
    parser.add_argument('--index_filename', required=True,
                        help='name of the new index file')
    parser.add_argument('--take_top_n', type=int, default=10,
                        help='number of classes in the pseudo-index file')
    args = parser.parse_args()

    create_index_file(args.pseudo_index_filename, args.index_filename, args.take_top_n)