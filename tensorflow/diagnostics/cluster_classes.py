import os
import numpy as np
import shutil
import collections
from diagnostics import heatmap_utils


def clusters(folder, filename, text_dtype, dtype):
    from sklearn.cluster import KMeans
    no_clusters = 10
    dimensions, matrix = heatmap_utils.read_matrix(os.path.join(folder, '{}.bin'.format(filename)), text_dtype, dtype)
    min_val, max_val = matrix.min(), matrix.max()
    #matrix = np.log10((matrix - min_val) / (max_val - min_val) * 9 + 1)
    matrix = np.power((matrix - min_val) / (max_val - min_val), 1/4)
    kmeans = KMeans(n_clusters=no_clusters, random_state=42, n_jobs=-1).fit(matrix)

    c = collections.Counter(kmeans.labels_)
    print(c)

    clusters_dir = 'bin/kmeans/clusters_' + str(no_clusters)
    os.mkdir(clusters_dir)
    for i in range(no_clusters):
        os.mkdir(os.path.join(clusters_dir, str(i)))

    for i in range(dimensions):
        file = os.listdir(os.path.join('/mnt/c/Users/Tom/Desktop/top10', str(i)))[0]
        #print(file)
        shutil.copyfile(os.path.join('/mnt/c/Users/Tom/Desktop/top10', str(i), file),
                        os.path.join(clusters_dir, str(kmeans.labels_[i]), str(i)+'.jpeg'))


def move_selected_ids(ids, source, dest):
    for id_ in ids:
        shutil.move(os.path.join(source, str(id_)), dest)


move_selected_ids([int(x.split('.')[0]) for x in
                   os.listdir('C:/Users/Tom/Workspace/KeywordSearch/tensorflow/bin/kmeans/clusters_10/3')
                   ], 'E:/selected_ids', 'E:/selected_ids_part')

# cluster 3
# py dataset/convert.py --dataset_dir="E:\selected_ids_part" --tfrecord_dir="E:/tfrecord_dir_part" --filename="train1390_C3-129" --parts=100 --take=800
# clusters('bin/covariance', 'covariance-train1390', 'f', np.float32)
