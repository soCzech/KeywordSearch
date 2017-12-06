import argparse
from simulations import simulation_utils, graph_utils
from common_utils import console


def perfect_user(images_filename, unnormalized_mean_filename, graph_filename, no_tries):
    images = simulation_utils.Images()
    images.read_images(images_filename)

    idf = simulation_utils.IDF()
    idf.read_term_count(unnormalized_mean_filename)
    idf.compute_idf()

    ranks = []
    pt = console.ProgressTracker()
    pt.reset(len(images.items()))

    pt.info(">> Calculating image ranks...")
    for i, image in images.items():
        for _ in range(no_tries):
            rand_index = simulation_utils.get_random_index_from_dist(image.DISTRIBUTION)
            rank = images.get_rank(image, rand_index)
            ranks.append(rank)
        pt.increment()

    graph_utils.plot_accumulative(ranks, graph_filename)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--perfect_user', action='store_true')
    parser.add_argument('-i', type=str)
    parser.add_argument('-u', type=str)
    parser.add_argument('-g', type=str)
    parser.add_argument('--no_tries', type=int, default=1)
    args = parser.parse_args()

    if args.perfect_user:
        perfect_user(args.i, args.u, args.g, args.no_tries)
