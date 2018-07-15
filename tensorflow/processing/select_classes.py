import os
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from PIL import Image as pImage, ImageDraw as pDraw, ImageFont as pFont
from nltk.corpus import wordnet as wn

from processing import classify
from common_utils import console, dataset, graph_utils, labels
import pickle


def create_clusters(deep_features, filename, image_dir, n_clusters=50):
    """
    Uses deep features to create clusters of synsets for easier selection.

    Args:
        deep_features: A location of the deep features file.
        filename: A location where to store the clusters.
        image_dir: A location where the images are located.
        n_clusters: Number of clusters to create.

    Returns:
        List of numpy arrays each containing ids for one cluster.
    """
    pt = console.ProgressTracker()
    pt.info(">> Reading deep features...")

    df = dataset.read_deep_features(deep_features)

    means = dict()
    for key in df.keys():
        means[key] = np.sum(df[key], axis=0) / len(df[key])

    keys, data = [key for key in sorted(means.keys())], [means[key] for key in sorted(means.keys())]

    pt.info(">> Computing PCA...")
    pca = PCA(n_components=2)
    pca_data = pca.fit_transform(data)

    pt.info(">> Computing K-Means...")
    kmeans = KMeans(init='k-means++', n_clusters=n_clusters, n_jobs=-1, random_state=42)
    kmeans.fit(data)

    centroids = pca.transform(kmeans.cluster_centers_)
    clusters = []
    for i in range(n_clusters):
        clusters.append(np.take(pca_data, np.where(kmeans.labels_ == i), axis=0)[0])

    graph_utils.plot_scatter(clusters, centroids, filename)

    pt.info(">> Creating custer images...")
    pt.reset(n_clusters)

    image_dims = (360, 270)

    if not os.path.exists(filename):
        os.mkdir(filename)

    synsets_in_clusters = []
    for cluster in range(n_clusters):
        os.mkdir(os.path.join(filename, str(cluster)))

        synsets = np.take(keys, np.where(kmeans.labels_ == cluster), axis=0)[0]
        synsets_in_clusters.append(synsets)

        for synset_id in synsets:
            image = pImage.new('RGB', (image_dims[0] * 2, image_dims[1] * 2 + 70), (255, 255, 255))
            canvas = pDraw.Draw(image)

            synset_str = "n" + str(synset_id).zfill(8)

            x, y = 0, 0
            for file in os.listdir(os.path.join(image_dir, synset_str))[:4]:
                img = pImage.open(os.path.join(image_dir, synset_str, file))
                img = img.resize((image_dims[0], image_dims[1]))
                image.paste(img, (x, y, x + image_dims[0], y + image_dims[1]))

                if x == image_dims[0]:
                    x = 0
                    y = image_dims[1]
                else:
                    x += image_dims[0]

            synset = wn.synset_from_pos_and_offset('n', synset_id)
            font = pFont.truetype("arial", 20)
            canvas.text((10, image_dims[1] * 2 + 10),
                        synset_str + ": " + ", ".join(synset.lemma_names()), fill=(0, 255, 0, 255), font=font)
            canvas.text((10, image_dims[1] * 2 + 40), synset.definition(), fill=(0, 255, 0, 255), font=font)

            image.save(os.path.join(filename, str(cluster),
                                    synset_str + "-" + ",".join(synset.lemma_names()).replace('/', '') + ".jpg"),
                       "JPEG")
        pt.increment()

    pt.info(">> Custer images created.")
    with open(filename + "-clusterdata.pickle", "wb") as f:
        pickle.dump((clusters, centroids, synsets_in_clusters), f)
    return synsets_in_clusters


def _generate_cluster_page(html_name, synset_ids, image_dir, html_directory):
    """Generates WordNet DAG html page for given synset ids.

    Args:
        html_name: Name of the html file.
        synset_ids: Synset ids to display in the graph.
        image_dir: A location of images of all the classes.
        html_directory: A location where the html components are stored.
    """
    pt = console.ProgressTracker()

    synsets = [wn._synset_from_pos_and_offset('n', key) for key in synset_ids]
    classes = labels.get_hypernyms(synsets)

    image_dir = os.path.abspath(image_dir)

    # `id`, `names`, `description`, `parents`, `children`, `images`, `no_images`, `selected`

    with open(os.path.join(html_directory, html_name + ".html"), 'w') as html_file:
        with open(os.path.join(html_directory, "components/index.html"), 'r') as template:
            for line in template:
                if line.strip() == "@$":
                    for key in sorted(classes):
                        c = classes[key]

                        if len(c.hypernyms) == 0:
                            if c.synset.wn_id != 1740:
                                pt.error("Synset {n{:08d} has no hypernyms.".format(c.synset.wn_id))
                                continue

                        images = []
                        for root, dirs, files in os.walk(image_dir):
                            for file in files:
                                if "n{:08d}".format(c.synset.wn_id) in file:
                                    images.append("file:///" + os.path.join(root, file).replace("\\", "/"))

                        hypernyms = ['n{:08d}'.format(i.synset.wn_id) for i in c.hypernyms]
                        hyponyms = ['n{:08d}'.format(i.synset.wn_id) for i in c.hyponyms]
                        html_file.write('n{:08d}: {{'
                                        'names: ["{}"],'
                                        'description: "{}",'
                                        'parents: [{}],'
                                        'children: [{}],'
                                        'images: [{}],'
                                        'no_images: {},'
                                        'shown: false,'
                                        'expanded: {},'
                                        'selected: false,'
                                        'visited: false,'
                                        'deleted: false'
                                        '}},\n'.format(
                            c.synset.wn_id, c.synset.name.replace('#', '", "'), c.synset.desc,
                            '"' + '", "'.join(hypernyms) + '"' if len(hypernyms) > 0 else "",
                            '"' + '", "'.join(hyponyms) + '"' if len(hyponyms) > 0 else "",
                            '"' + '", "'.join(images) + '"' if len(images) > 0 else "",
                            1000 if len(images) > 0 else 0,
                            "false" if c.synset.wn_id == 1740 else "true"
                        ))
                else:
                    html_file.write(line)


def generate_cluster_pages(synsets_lists, image_folder, components_folder):
    """Generates WordNet DAG html page for each cluster.

    Args:
        synsets_lists: A list of lists of synset ids.
        image_folder: A location of images of all the classes.
        components_folder: A location where the html components are stored.
    """
    pt = console.ProgressTracker()
    pt.info(">> Generating html pages...")
    pt.reset(len(synsets_lists))

    for i in range(len(synsets_lists)):
        synsets = synsets_lists[i]
        _generate_cluster_page("{:03d}".format(i), synsets, image_folder, components_folder)
        pt.increment()


def get_images_for_each_class(directory, images_per_class=10):
    """Reads images in given directory.

    Args:
        directory: Directory where the images are located.
        images_per_class: Number of images to take per class.

    Returns:
        Dictionary of (image path, class id).
    """
    res = dict()

    sorted_list = sorted(os.listdir(directory))
    pt = console.ProgressTracker()
    pt.info(">> Reading image files...")
    pt.reset(len(sorted_list))

    for folder in sorted_list:
        if os.path.isdir(os.path.join(directory, folder)):
            i = 0
            for image in sorted(os.listdir(os.path.join(directory, folder))):
                filename = os.path.join(directory, folder, image)
                if os.stat(filename).st_size > 0:
                    res[filename] = int(folder[1:])
                    i += 1
                else:
                    pt.error(filename + ", taking different file.")
                    continue

                if i == images_per_class:
                    break
        pt.increment()
    return res


if __name__ == '__main__':
    dir_of_synset_ids_of_images = ""
    imagenet_checkpoint = ""
    component_dir = ""
    where_to_store_clusters = ""

    images = get_images_for_each_class(dir_of_synset_ids_of_images)
    classify.run(
        images, 1001, imagenet_checkpoint, where_to_store_clusters
    )

    synsets = create_clusters(
        where_to_store_clusters + ".deep-features",
        where_to_store_clusters, dir_of_synset_ids_of_images
    )
    generate_cluster_pages(
        synsets, where_to_store_clusters, component_dir
    )
