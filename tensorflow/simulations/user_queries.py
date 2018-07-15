from common_utils import console


class Label:
    """
    A class representing one label.
    """
    ID = None
    SYNSET_ID = None
    NAMES = None
    HYPONYMS = []
    HYPERNYMS = []
    DESCRIPTION = None

    @staticmethod
    def read_labels(filename):
        """
        Args:
            filename: location of the label file.

        Returns:
            A dictionary of (synset id, label object).
        """
        labels = dict()

        with open(filename, 'r') as f:
            for line in f:
                parts = line.split('~')
                if len(parts) != 6:
                    raise Exception()

                l = Label()
                l.SYNSET_ID = int(parts[1])
                l.NAMES = parts[2].split('#')
                if parts[0] != "H":
                    l.ID = int(parts[0])
                if parts[3] != "":
                    l.HYPONYMS = [int(i) for i in parts[3].split('#')]
                if parts[4] != "":
                    l.HYPERNYMS = [int(i) for i in parts[4].split('#')]
                l.DESCRIPTION = parts[5]

                labels[l.SYNSET_ID] = l
        return labels

    @staticmethod
    def expand_query(labels, query):
        """
        Takes a query in form of synset ids and returns expanded query in label ids.

        Args:
            labels: labels dictionary.
            query: a list of (synset id, bool if to use hyponyms).

        Returns:
            A list of label ids.
        """

        def expand_hyponyms(hyponyms):
            l = []
            for h in hyponyms:
                if labels[h].ID is not None:
                    l.append(labels[h].ID)
                l.extend(expand_hyponyms(labels[h].HYPONYMS))
            return l

        l = []
        for synset_id, use_children in query:
            if use_children:
                if labels[synset_id].ID is not None:
                    l.append(labels[synset_id].ID)
                l.extend(expand_hyponyms(labels[synset_id].HYPONYMS))
            else:
                l.append(labels[synset_id].ID)
        return list(set(l))


# region Parsing user queries

def read_queries(filename):
    """
    Reads user generated queries.

    Args:
        filename: file to read the queries from.
    Returns:
        List of tuples.
        A frame id.
        A list of tuples: integer representing synset id and boolean specifying if hyponyms shall be used.
    """
    queries = []
    with open(filename, "r") as f:
        for line in f:
            frame_id, query = line.split("~")
            frame_id = int(frame_id)
            query = [
                (int(label.split(":")[0]), int(label.split(":")[1]) == 1)
                for label in query.split(",")
            ]
            queries.append((frame_id, query))
    return queries


def parse_queries(query_log_filename, label_filename):
    """
    Reads and parses user generated queries.

    Args:
        query_log_filename: log file to read the queries from.
        label_filename: label file to read WordNet structure from.
    Returns:
        A tuple.
        A list of samples (frame ids).
        A list of corresponding indexes.
    """
    pt = console.ProgressTracker()
    pt.info(">> Parsing queries...")

    labels = Label.read_labels(label_filename)
    samples = []
    indexes = []
    queries = read_queries(query_log_filename)

    for frame_id, query in queries:
        samples.append(frame_id)
        indexes.append(Label.expand_query(labels, query))

    return samples, indexes

# endregion
# s, i = parse_queries("C:\\Users\\Tom\\Workspace\\KeywordSearch\\data\\simulation\\anotated_frames.txt", "C:\\Users\\Tom\\Workspace\\KeywordSearch\\data\\content\\ITEC\\BC-ITEC-GoogLeNet.label")
# print(len(s))
# print(sum([len(a) for a in i]))
# print(sum([len(a) for a in i])/float(len(s)))