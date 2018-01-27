import os
import xml.etree.ElementTree as ET
from common_utils import console
import struct
import argparse
import re
import pickle


VIDEO_BASE_INDEX = 35345


def get_file_ids(filename):
    tree = ET.parse(filename)
    root = tree.getroot()

    l = {}
    for file in root.iter('VideoFile'):
        fid = int(file.find('id').text) - VIDEO_BASE_INDEX
        l[fid] = file.find('filename').text
    return l


class WordSegment:
    def __init__(self):
        self.words = dict()
        self.start = 0
        self.end = 0
        self.lang = "None"


def get_word_segment_list(filename):
    if filename is None:
        return []

    tree = ET.parse(filename)
    root = tree.getroot().find('SegmentList')

    seg = []
    for segment in root.iter('SpeechSegment'):
        ws = WordSegment()
        ws.lang = segment.get('lang')
        ws.start = float(segment.get('stime'))
        ws.end = float(segment.get('etime'))

        for word in segment.iter('Word'):
            t = word.text.strip().lower()
            if t[0] == '{' or not re.search('[a-zA-Z0-9]', t):
                continue

            if t in ws.words:
                ws.words[t] += 1
            else:
                ws.words[t] = 1

        seg.append(ws)
    return seg


def find_transcript_file(directory, name):
    name = os.path.splitext(name)[0]

    for file in os.listdir(directory):
        if file.startswith(name):
            return os.path.join(directory, file)

    pt = console.ProgressTracker()
    pt.info("\t! File '" + name + "' not found.")
    return None


class Video:
    def __init__(self):
        self.id = 0
        self.frames = []


class VideoFrame:
    def __init__(self):
        self.timestamp = 0
        self.path = "/"
        self.id = 0
        self.start = 0
        self.end = 0
        self.words = dict()


def get_video_info_from_image_files(directory):
    directory = os.path.normpath(directory)
    image_id = 0

    pt = console.ProgressTracker()
    pt.info(">> Reading video frames...")
    vid_dirs = sorted(os.listdir(directory))
    pt.reset(len(vid_dirs))

    res = dict()
    for folder in vid_dirs:
        if os.path.isdir(os.path.join(directory, folder)):
            v = Video()
            v.id = int(folder) - VIDEO_BASE_INDEX

            for image in sorted(os.listdir(os.path.join(directory, folder))):
                vf = VideoFrame()
                vf.id = image_id
                vf.timestamp = float(image.split('_')[2][:-3])

                span = float(image.split('_')[4][1:].split('.')[0]) / 4 / 2
                vf.start = max(0.0, vf.timestamp - span)
                vf.end = vf.timestamp + span

                vf.path = os.path.join(directory, folder, image)
                v.frames.append(vf)
                image_id += 1

            res[v.id] = v

        pt.increment()
    return res


def get_segments_for_video_frame(frame, segments, start_from):
    while start_from < len(segments):
        if frame.end >= segments[start_from].start and frame.start <= segments[start_from].end:
            break
        start_from += 1

    if start_from == len(segments):
        frame.words = None
    elif segments[start_from].lang == "eng-usa":
        frame.words = segments[start_from].words

    return start_from


def create_label_and_index_files(video_dir, master_file, label_file, pseudo_index_file):
    words = set()

    dataset = get_video_info_from_image_files(video_dir)
    vid_ids_to_transcript_files = get_file_ids(master_file)

    directory = os.path.join(os.path.dirname(master_file), 'asr/xml')
    pt = console.ProgressTracker()
    pt.info(">> Reading video transcripts...")
    pt.reset(len(vid_ids_to_transcript_files))

    for index in sorted(vid_ids_to_transcript_files.keys()):
        vid_filename = find_transcript_file(directory, vid_ids_to_transcript_files[index])
        segments = get_word_segment_list(vid_filename)

        start_from = 0
        for vf in dataset[index].frames:
            start_from = get_segments_for_video_frame(vf, segments, start_from)

        for s in segments:
            if s.lang != "eng-usa":
                continue
            for word in s.words.keys():
                words.add(word)
        pt.increment()

    pt.info(">> Creating label file...")

    classes = zip(range(len(words)), sorted(words))
    dictionary = {}
    with open(label_file, 'w', encoding="utf-8") as f:
        for index, cls in classes:
            dictionary[cls] = index
            f.write('{:d}~{:d}~{}~~~\n'.format(index, index, cls))

    pt.info(">> Creating pseudo index file...")
    pt.reset(len(dataset))

    with open(pseudo_index_file, 'wb') as f:
        for video_id in dataset.keys():
            for vf in dataset[video_id].frames:
                if vf.words is None or len(vf.words) == 0:
                    continue

                f.write(struct.pack('<I', vf.id))
                f.write(struct.pack('<I', len(vf.words)))

                for word in vf.words.keys():
                    f.write(struct.pack('<I', dictionary[word]))
                for word in vf.words.keys():
                    f.write(struct.pack('<f', float(vf.words[word])))
            pt.increment()

    pt.info(">> Pseudo index created.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-vf', type=str, required=True)
    parser.add_argument('-mf', type=str, required=True)
    parser.add_argument('-lf', type=str, required=True)
    parser.add_argument('-pf', type=str, required=True)
    args = parser.parse_args()

    create_label_and_index_files(args.vf, args.mf, args.lf, args.pf)

# py deployment/app/parse_audio_transcript.py -mf C:/Users/Tom/Desktop/transcript/iacc.3.collection.xml -lf label.del -pf index.del -vf E:/images-4fps-selected/
