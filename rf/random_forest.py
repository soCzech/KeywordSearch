from sklearn.ensemble import RandomForestClassifier
import pickle
import os
import struct
import rf.signature


def evaluate(classifier, signature_dir, dataset_name):
    signatures, labels = get_data(signature_dir, dataset_name)

    classifier.score(signatures, labels)


def train(classifier, signature_dir, dataset_name):
    signatures, labels = get_data(signature_dir, dataset_name)

    classifier.fit(signatures, labels)
    return classifier


def get_classifier(bin_dir, name, estimators=10, max_depth=None):
    file = os.path.join(bin_dir, '{}.pkl'.format(name))
    if os.path.isfile(file):
        return pickle.load(file)
    return RandomForestClassifier(n_estimators=estimators, criterion='gini', max_depth=max_depth, min_samples_split=2,
                                  n_jobs=-1, random_state=42, warm_start=True)


def save_classifier(classifier, bin_dir, name):
    pickle.dump(classifier, os.path.join(bin_dir, '{}.pkl'.format(name)))


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
    cls = get_classifier('bin', 'rf_test')
    cls = train(cls, './', 'test_all_but5')
    evaluate(cls, './', 'eval5')
    save_classifier(cls, 'bin', 'rf_test')
