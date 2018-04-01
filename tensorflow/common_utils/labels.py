from nltk.corpus import wordnet as wn


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


def create_labels(synsets_to_ids, label_file):
    synsets = [wn.synset_from_pos_and_offset('n', int(synset_id[1:])) for synset_id, _ in synsets_to_ids.items()]
    classes = get_hypernyms(synsets)

    with open(label_file + ".mapping.txt", 'w') as f:
        for key in sorted(synsets_to_ids):
            f.write("{}:{:04d}\n".format(key, synsets_to_ids[key]))

    with open(label_file + ".label", 'w') as f:
        for k in sorted(classes):
            c = classes[k]
            if type(c) is Hypernym:
                f.write('H~{:08d}~{}~{}~~{}\n'.format(
                    c.synset.wn_id, c.synset.name, '#'.join([str(x.synset.wn_id) for x in c.hyponyms]), c.synset.desc)
                )
            else:
                f.write('{:d}~{:08d}~{}~{}~{}~{}\n'.format(
                    synsets_to_ids["n{:08d}".format(k)], c.synset.wn_id, c.synset.name,
                    '#'.join([str(x.synset.wn_id) for x in c.hyponyms]),
                    '#'.join([str(x.synset.wn_id) for x in c.hypernyms]), c.synset.desc)
                )
