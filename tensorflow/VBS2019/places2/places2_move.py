import os
import shutil


map = {}
mapping = os.path.normpath("D:/Datasets/Places2/mapping.txt")

with open(mapping, "r") as f:
    for line in f:
        line = line.strip("\n").split(":")
        map[line[0]] = line[1]


directory = os.path.normpath("D:/Datasets/Places2/Standard (Core)/train/data_large")


if __name__ == "__main__":
    for key in map.keys():
        if "-" not in key:
            src = os.path.join(directory, key)
        else:
            split = key.split("-")
            src = os.path.join(directory, split[0], split[1])

        dst = os.path.join(directory, "{}.places2.{}".format(map[key], key))
        shutil.move(src, dst)
        print("{} moved to {}".format(src, dst))
