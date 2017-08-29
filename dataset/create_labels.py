import argparse
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


def get_hypernyms(synset_id_file):
    classes = {}
    synsets = load_synsets(synset_id_file)

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
    classes = get_hypernyms(synset_id_file)

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
    classes = get_hypernyms(synset_id_file)

    def _print_hyponyms_helper(c, string):
        count = 0

        string = string + ' ~ ' + c.synset.names[0]
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
