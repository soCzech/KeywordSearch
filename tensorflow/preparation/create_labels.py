import argparse
from nltk.corpus import wordnet as wn
# https://stackoverflow.com/questions/8077641/how-to-get-the-wordnet-synset-given-an-offset-id


class Synset:
    """
    A class representing one WordNet synset.
    """
    def __init__(self, wn_id, names, desc):
        self.wn_id = wn_id
        self.names = names
        self.name = "#".join(names).replace("_", " ")
        self.desc = desc


class Hypernym:
    """
    A class representing an empty node in a tree.
    """
    def __init__(self, synset):
        self.hypernyms = []
        self.hyponyms = []
        self.synset = synset


class ImageClass:
    """
    A class representing a class node in a tree.
    """
    def __init__(self, local_id, synset):
        self.hypernyms = []
        self.hyponyms = []
        self.local_id = local_id
        self.synset = synset
        self.visited = False


def load_synsets(synset_id_file):
    """
    Takes all file with synset ids and returns a list of synsets.
    """
    synsets = []
    with open(synset_id_file, "r") as f:
        synset_id = f.readline()
        while synset_id != "":
            synset_id = int(synset_id[1:])
            synset = wn._synset_from_pos_and_offset("n", synset_id)

            synsets.append(synset)
            synset_id = f.readline()
    return synsets


def get_hypernyms(synsets):
    """
    Constructs a tree (or DAG) of class relations and adds hypernyms.
    """
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


def create_labels(synset_file, label_file):
    """
    Creates label file based on all synsets in the `synset_file`.
    """
    synsets = load_synsets(synset_file)
    classes = get_hypernyms(synsets)

    with open(label_file, "w") as f:
        i = 0
        for k in sorted(classes):
            c = classes[k]
            if type(c) is Hypernym:
                f.write("H~{:08d}~{}~{}~~{}\n".format(c.synset.wn_id, c.synset.name,
                                                      "#".join([str(x.synset.wn_id) for x in c.hyponyms]),
                                                      c.synset.desc))
            else:
                f.write("{:d}~{:08d}~{}~{}~{}~{}\n".format(i, c.synset.wn_id, c.synset.name,
                                                           "#".join([str(x.synset.wn_id) for x in c.hyponyms]),
                                                           "#".join([str(x.synset.wn_id) for x in c.hypernyms]),
                                                           c.synset.desc))
                i += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--synset_file", required=True,
                        help="path to a file containing WordNet ids")
    parser.add_argument("--label_file", required=True,
                        help="label file to store labels to")
    args = parser.parse_args()

    create_labels(args.synset_file, args.label_file)
