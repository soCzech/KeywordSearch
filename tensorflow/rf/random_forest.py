import argparse
from sklearn.ensemble import RandomForestClassifier
import pickle
import os
import struct
import rf.signature
import numpy as np
from models import model_utils
# https://stackoverflow.com/questions/6910641/how-to-get-indices-of-n-maximum-values-in-a-numpy-array


def in_top_k(vector, label, k):
    if len(vector) < k:
        return False
    return label in np.argpartition(vector, -k)[-k:]


def evaluate(classifier, signature_dir, dataset_name, bin_dir):
    signatures, labels = get_data(signature_dir, dataset_name)

    trees = [e.tree_.max_depth for e in classifier.estimators_]

    probabilities = classifier.predict_proba(signatures)
    top1, top5, top10 = 0, 0, 0

    for l, p in zip(labels, probabilities):
        if in_top_k(p, l, 10):
            top10 += 1
        if in_top_k(p, l, 5):
            top5 += 1
        if np.argmax(p) == l:
            top1 += 1

    model_utils.write_evaluation(os.path.join(bin_dir, 'evaluation_rf.txt'),
                                 [('#Images', len(signatures), '{:16d}'), ('Top1Count', top1, '{:16d}'),
                                  ('Top5Count', top5, '{:16d}'), ('Top10Count', top10, '{:16d}'),
                                  ('#Trees', len(trees), '{:16d}'), ('TreeMaxDepth', max(trees), '{:16d}'),
                                  ('TreeMinDepth', min(trees), '{:16d}'),
                                  ('TreeAvgDepth', sum(trees)/len(trees), '{:16.2f}')])


def train(classifier, signature_dir, dataset_name):
    signatures, labels = get_data(signature_dir, dataset_name)

    classifier.fit(signatures, labels)
    return classifier


def get_classifier(bin_dir, name, estimators=10, max_depth=None):
    if name:
        file = os.path.join(bin_dir, '{}.pkl'.format(name))
        if os.path.isfile(file):
            with open(file, 'rb') as f:
                return pickle.load(f)
    return RandomForestClassifier(n_estimators=estimators, criterion='gini', max_depth=max_depth, min_samples_split=2,
                                  n_jobs=-1, random_state=42, warm_start=True, verbose=2)


def save_classifier(classifier, bin_dir, name):
    with open(os.path.join(bin_dir, '{}.pkl'.format(name)), 'wb') as f:
        pickle.dump(classifier, f)


def get_data(signature_dir, dataset_name):
    signatures = []
    labels = []

    with open(os.path.join(os.path.normpath(signature_dir), '{}.signatures'.format(dataset_name)), 'rb') as f:
        raw_id = f.read(4)
        while raw_id != b'':
            label = struct.unpack('<I', raw_id)[0]
            signature = struct.unpack(rf.signature.signature_format, f.read(4 * rf.signature.signature_size))

            signatures.append(signature)
            labels.append(label)

            raw_id = f.read(4)
    return signatures, labels


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--train',
                        help='a name of the signatures file')
    parser.add_argument('--evaluate',
                        help='a name of the signatures file')
    parser.add_argument('--signature_dir', required=True,
                        help='directory where to find signatures')
    parser.add_argument('--bin_dir', default='bin',
                        help='directory containing stored forest')
    parser.add_argument('--model_name',
                        help='filename of the forest file to load/store')
    parser.add_argument('--n_estimators', type=int, default=10,
                        help='number of trees in forest')
    parser.add_argument('--max_depth', type=int, default=None,
                        help='maximal depth of each tree')
    args = parser.parse_args()

    cls = get_classifier(args.bin_dir, args.model_name, estimators=args.n_estimators, max_depth=args.max_depth)
    if args.train:
        cls = train(cls, args.signature_dir, args.train)
    if args.evaluate:
        evaluate(cls, args.signature_dir, args.evaluate, args.bin_dir)
    if args.model_name:
        save_classifier(cls, args.bin_dir, args.model_name)
