import os
from deployment import index_utils


def prepare_for_web(pseudo_index_filename, destination, num_classes_per_image, max_photos=48, min_prob=0):
    classes = index_utils.get_class_representatives(pseudo_index_filename, num_classes_per_image)
    sorted_classes = sorted(classes)

    sql = open(os.path.join(destination, 'top_images_by_class.sql'), 'w')
    sh = open(os.path.join(destination, 'top_images_by_class-copy_to_web.sh'), 'w')

    sh.write('LOCATION=\nDESTINATION=\n')
    sql.write("INSERT INTO `evaluation` (`image_name`, `class`, `probability`, `selected`) VALUES\n")

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