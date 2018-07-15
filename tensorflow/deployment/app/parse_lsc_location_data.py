import struct
import xml.etree.ElementTree as ET
from common_utils import dataset
from common_utils.dataset import DEFAULT_HEADER
HEADER = DEFAULT_HEADER


def date_to_id(filename):
    with open(filename, "r") as f:
        id = 0
        d = {}
        for line in f:
            n = line.split("d")[1][:-1]
            d[n] = id
            id += 1
        return d


def get_word_segment_list(filename, dictionary):
    if filename is None:
        return []

    tree = ET.parse(filename)
    days = tree.getroot().getchildren()[0].getchildren()[0].getchildren()[0].getchildren()

    seg = []
    for day in days:
        for minute in day.find("minutes").iter("minute"):
            if minute.find("location") is None or minute.find("location").find("name") is None:
                continue
            loc = minute.find("location").find("name").text

            if minute.find("images") is None:
                continue
            for img in minute.find("images").getchildren():
                img_name = img.find("image-path").text.split("/")[-1]
                if img_name in dictionary:
                    seg.append((dictionary[img_name], loc))
    seg.sort(key=lambda t: t[0])
    return seg


def create_index(pairs, label_file, pseudo_index_file):
    words = sorted(set([x for _, x in pairs]))
    classes = zip(range(len(words)), words)

    dictionary = {}
    with open(label_file, 'w', encoding="utf-8") as f:
        for index, cls in classes:
            dictionary[cls] = index
            f.write('{:d}~{:d}~{}~~~\n'.format(index, index, cls))

    with dataset.create_file(pseudo_index_file, [('<I', len(words))], HEADER) as f:
        for id_, class_ in pairs:
            f.write(struct.pack('<I', id_))
            f.write(struct.pack('<I', 1))

            f.write(struct.pack('<I', dictionary[class_]))
            f.write(struct.pack('<f', float(1)))

if __name__ == "__main__":
    d = date_to_id("C:\\Users\\Tom\\Workspace\\ViretTool\\TestData\\LSC2018\\images-224\\filelist.txt")
    r = get_word_segment_list("C:\\Users\\Tom\\Workspace\\ViretTool\\TestData\\LSC2018\\LSC2018_dataset\\LSC2018_metadata.xml", d)

    print(r[:10])
    print(r[-10:])

    create_index(r, "C:\\Users\\Tom\\Workspace\\ViretTool\\TestData\\LSC2018\\images-224\\LSC2018-location.label", "C:\\Users\\Tom\\Workspace\\ViretTool\\TestData\\LSC2018\\images-224\\pseudo-index")
