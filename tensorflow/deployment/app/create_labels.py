import argparse
import sys
import os
import struct
from deployment import index_utils
from nltk.corpus import wordnet as wn
# https://stackoverflow.com/questions/8077641/how-to-get-the-wordnet-synset-given-an-offset-id


class Synset:
    def __init__(self, wn_id, names, desc):
        self.wn_id = wn_id
        self.names = names
        self.name = '#'.join(names).replace('_', ' ')
        self.desc = desc


class Hypernym:
    def __init__(self, synset):
        self.hypernyms = []
        self.hyponyms = []
        self.synset = synset


class ImageClass:
    def __init__(self, local_id, synset):
        self.hypernyms = []
        self.hyponyms = []
        self.local_id = local_id
        self.synset = synset
        self.visited = False


def load_synsets(synset_id_file):
    synsets = []
    with open(synset_id_file, 'r') as f:
        synset_id = f.readline()
        while synset_id != '':
            synset_id = int(synset_id[1:])
            synset = wn._synset_from_pos_and_offset('n', synset_id)

            synsets.append(synset)
            synset_id = f.readline()
    return synsets


def get_hypernyms(synsets):
    classes = {}

    def _get_hypernyms_helper(synset, classes):
        for hm in synset.hypernyms():
            if hm.offset() in classes:
                classes[hm.offset()].hyponyms.append(classes[synset.offset()])
            else:
                classes[hm.offset()] = Hypernym(Synset(hm.offset(), hm.lemma_names(), hm.definition()))
                classes[hm.offset()].hyponyms.append(classes[synset.offset()])
                _get_hypernyms_helper(hm, classes)

            classes[synset.offset()].hypernyms.append(classes[hm.offset()])

    for synset in synsets:
        new_class = ImageClass(0, Synset(synset.offset(), synset.lemma_names(), synset.definition()))

        if synset.offset() in classes:
            new_class.hyponyms = classes[synset.offset()].hyponyms
        classes[synset.offset()] = new_class

        _get_hypernyms_helper(synset, classes)
    return classes


def create_labels(synset_id_file, label_file):
    synsets = load_synsets(synset_id_file)
    classes = get_hypernyms(synsets)

    with open(label_file, 'w') as f:
        i = 0
        for k in sorted(classes):
            c = classes[k]
            if type(c) is Hypernym:
                f.write('H~{:08d}~{}~{}~~{}\n'.format(c.synset.wn_id, c.synset.name,
                                                      '#'.join([str(x.synset.wn_id) for x in c.hyponyms]),
                                                      c.synset.desc))
            else:
                f.write('{:d}~{:08d}~{}~{}~{}~{}\n'.format(i, c.synset.wn_id, c.synset.name,
                                                           '#'.join([str(x.synset.wn_id) for x in c.hyponyms]),
                                                           '#'.join([str(x.synset.wn_id) for x in c.hypernyms]),
                                                           c.synset.desc))
                i += 1


def print_hyponyms(synset_id_file, wn_id):
    synsets = load_synsets(synset_id_file)
    classes = get_hypernyms(synsets)

    def _print_hyponyms_helper(c, string):
        count = 0

        string = '{} ~ {} (n{:08d})'.format(string, c.synset.names[0], c.synset.wn_id)
        if type(c) is ImageClass:
            if not c.visited:
                c.visited = True
                count += 1
                print(string)
        for h in c.hyponyms:
            count += _print_hyponyms_helper(h, string)
        return count

    print('Number of hyponyms found: ' + str(_print_hyponyms_helper(classes[wn_id], '')))

    count_missing = 0
    for a in classes:
        if type(classes[a]) is ImageClass and not classes[a].visited:
            count_missing += 1
    print('Number of classes that are not hyponyms: ' + str(count_missing))


def load_synset_file(filename):
    synsets = {}
    with open(filename, 'r') as f:
        for line in f:
            split = line.split(':')
            synsets[int(split[0][1:])] = int(split[1])
    return synsets


# egrep '(version="fall2011"|version="winter11")' ReleaseStatus.xml | sed -e 's/.*wnid="n/n/' |
#   sed 's/" released.*numImages=/:/' | sed -e 's/"//' -e 's:" />::'
#   > /mnt/c/Users/Tom/Workspace/KeywordSearch/tensorflow/bin/all_synsets_imagenet.txt
def all_synsets_to_sql(filename, synset_file, image_dir):
    synsets_to_no_images = load_synset_file(synset_file)
    synsets = [wn._synset_from_pos_and_offset('n', key) for key in synsets_to_no_images]
    classes = get_hypernyms(synsets)

    print(str(len(classes)))

    with open(filename, 'w') as f:
        f.write("INSERT INTO `tree` (`id`, `names`, `description`, `parents`, `children`, `images`, `no_images`, `selected`)" +
                " VALUES\n")

        first = True
        for key in sorted(classes):
            c = classes[key]

            if len(c.hypernyms) == 0:
                print(str(c.synset.wn_id))

                if c.synset.wn_id != 1740:
                    continue

            directory = os.path.join(image_dir, 'n{:08d}'.format(c.synset.wn_id))
            files = ""
            if os.path.isdir(directory):
                files = ",".join(os.listdir(directory))

            if first:
                first = False
            else:
                f.write(",\n")
            f.write("('n{:08d}', '{}', '{}', '{}', '{}', '{}', {:d}, '0')".format(
                c.synset.wn_id, c.synset.name.replace("'", "\\'"), c.synset.desc.replace("'", "\\'"),
                '#'.join(['n{:08d}'.format(i.synset.wn_id) for i in c.hypernyms]),
                '#'.join(['n{:08d}'.format(i.synset.wn_id) for i in c.hyponyms]), files,
                synsets_to_no_images[key] if key in synsets_to_no_images else 0
            ))
        f.write(";\n")
#all_synsets_to_sql('bin/tree.sql', 'bin/all_synsets_imagenet.txt', 'W:/imagenet/synsets')


def create_labels_from_annotations(directory, label_file, pseudo_index_file):
    annotations = index_utils.list_annotation_files(directory)
    classes = set()
    files = []

    for index, file in enumerate(annotations):
        sys.stdout.write('\rSearching for labels in {} ({:d}/{:d}).'.format(file, index, len(annotations)))
        sys.stdout.flush()

        file_cls, file_prob = [], []
        l = index_utils.read_annotation_file(file, max_no=None, max_prob=None)
        for ind2, (cls, prob) in enumerate(l):
            if ind2 < 10:
                classes.add(cls)
                file_cls.append(cls)
                file_prob.append(prob)
        files.append((file, file_cls, file_prob))

    sys.stdout.write('\rCreating label file.\n')
    sys.stdout.flush()

    classes = zip(range(len(classes)), sorted(classes))
    dictionary = {}
    with open(label_file, 'w') as f:
        for index, cls in classes:
            dictionary[cls] = index
            f.write('{:d}~{:d}~{}~~~\n'.format(index, index, cls))

    with open(pseudo_index_file, 'wb') as f:
        for file, cls, prob in files:
            f.write(struct.pack('<I', index_utils.filename_to_id(file)))
            for c in cls:
                f.write(struct.pack('<I', dictionary[c]))
            for p in prob:
                f.write(struct.pack('<f', p))


#create_labels_from_annotations("c:\\Users\\Tom\\Workspace\\KeywordSearch\\annotation\\", "bin/classes.labels-deepfeatures", "bin/files.pseudo-index-deepfeatures")

# 1740 is entity - should contain all classes
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--synset_id_file', required=True,
                        help='path to a file containing WordNet ids')
    parser.add_argument('--create_labels',
                        help='creates label file with name as an argument')
    parser.add_argument('--print_hyponyms', type=int,
                        help='print tree of hyponyms given a synset id')
    args = parser.parse_args()

    if args.create_labels:
        create_labels(args.synset_id_file, args.create_labels)
    if args.print_hyponyms:
        print_hyponyms(args.synset_id_file, args.print_hyponyms)
