import os
import sys
from nltk.corpus import wordnet as wn


synsets = list(wn.all_synsets())

sel_syns = set()
selected_synsets = "C:/Users/Tom/Workspace/KeywordSearch/data/preprocessing/results/selected_synsets.txt"

if os.path.exists(selected_synsets):
    with open(selected_synsets, "r") as f:
        for line in f:
            sel_syns.add(line.strip("\n"))


def search(query, out=sys.stdout):
    for s in synsets:
        prnt = False
        for lemma in s.lemmas():
            if (query[0] == "!" and query[1:] == lemma.name()) or (query[0] != "!" and query in lemma.name()):
                prnt = True
                break

        if prnt:
            lemmas = ", ".join([lemma.name() for lemma in s.lemmas()])
            sid = "n{:08d}".format(s.offset())
            desc = s.definition()

            if out != sys.stdout:
                line = "{0} {1:62} {2}".format(sid, lemmas[:60], desc).replace(" ", "&nbsp;")
                if sid in sel_syns:
                    line = "<span style=\"color:red\">" + line + "</span>"
                print(line, file=out)
                print("<br>", file=out)
            else:
                print("{:3} {} {:62} {}".format("[X]" if sid in sel_syns else "", sid, lemmas[:60], desc[:150]))

    if out == sys.stdout:
        print("---")


if __name__ == "__main__":
    while True:
        query = input("Search: ")
        search(query)
