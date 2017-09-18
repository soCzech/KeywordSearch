import os
import struct
import argparse


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

            for ind, val in zip(image_indices, image_values):
                if ind not in classes:
                    classes[ind] = [(image_id, val)]
                else:
                    classes[ind].append((image_id, val))
    return classes


def create_index_file(pseudo_index_filename, index_filename, num_classes_per_image):
    classes = get_class_representatives(pseudo_index_filename, num_classes_per_image)
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


def prepare_for_web(pseudo_index_filename, destination, num_classes_per_image, max_photos=48, min_prob=0):
    classes = get_class_representatives(pseudo_index_filename, num_classes_per_image)
    sorted_classes = sorted(classes)

    sql = open(os.path.join(destination, 'top_images_by_class.sql'), 'w')
    sh = open(os.path.join(destination, 'top_images_by_class-copy_to_web.sh'), 'w')

    sh.write('LOCATION=\nDESTINATION=\n')
    sql.write("INSERT INTO `comparison` (`image_name`, `class`, `probability`, `dataset`) VALUES\n")

    first = True
    for key in sorted_classes:
        photos = classes[key]
        photos.sort(key=lambda tup: -tup[1])

        sh.write('mkdir ${{DESTINATION}}/{}\n'.format(key))
        for index, (photo_id, photo_val) in enumerate(photos):
            if index >= max_photos:
                break
            if photo_val < min_prob:
                break

            if not first:
                sql.write(',\n')
            else: first = False

            sh.write('cp ${{LOCATION}}/{0}.jpg ${{DESTINATION}}/{1}/{0}.jpg\n'.format(photo_id, key))
            sql.write("('{}.jpg', '{}', '{}', '0')".format(photo_id, key, photo_val))

    sql.write(';\n')
    sql.close()
    sh.close()

#prepare_for_web('bin/files.pseudo-index', 'bin', 10, max_photos=3, min_prob=0)

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