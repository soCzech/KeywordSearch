import numpy as np
import matplotlib as mpl
from common_utils import console
mpl.use("pgf")
import matplotlib.pyplot as plt


def fig_size(scale):
    fig_width_pt = 469.755  # Get this from LaTeX using \the\textwidth
    inches_per_pt = 1.0 / 72.27  # Convert pt to inch
    golden_mean = (np.sqrt(5.0) - 1.0) / 2.0  # Aesthetic ratio (you could change this)
    fig_width = fig_width_pt * inches_per_pt * scale  # width in inches
    fig_height = fig_width * golden_mean  # height in inches
    return [fig_width, fig_height]


def pgf_with_latex():
    return {  # setup matplotlib to use latex for output
        "pgf.texsystem": "pdflatex",  # change this if using xetex or lautex
        "text.usetex": True,  # use LaTeX to write all text
        "font.family": "serif",
        "font.serif": [],  # blank entries should cause plots to inherit fonts from the document
        "font.sans-serif": [],
        "font.monospace": [],
        "axes.labelsize": 10,  # LaTeX default is 10pt font.
        "text.fontsize": 10,
        "legend.fontsize": 8,  # Make the legend/label fonts a little smaller
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "figure.figsize": fig_size(0.9),  # default fig size of 0.9 textwidth
        "pgf.preamble": [
            r"\usepackage[utf8x]{inputenc}",  # use utf8 fonts becasue your computer can handle it :)
            r"\usepackage[T1]{fontenc}",  # plots will be generated using this preamble
        ]
    }
mpl.rcParams.update(pgf_with_latex())


def new_fig(width):
    plt.clf()
    fig = plt.figure(figsize=fig_size(width))
    ax = fig.add_subplot(111)
    # plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9)
    return fig, ax


def save_fig(filename):
    plt.savefig('{}.pgf'.format(filename))
    plt.savefig('{}.pdf'.format(filename))


def plot_accumulative(ranks, graph_filename, figure_size=0.9):
    pt = console.ProgressTracker()
    pt.info(">> Plotting a graph...")

    fig, ax = new_fig(figure_size)

    ranks.sort(key=lambda r: r if r is not None else 2147483648 - 1)
    x, y = [], []
    i = 0

    for rank in ranks:
        if rank is None:
            break
        i += 1
        x.append(rank)
        y.append(i/len(ranks)*100)

    ax.step(x, y, where='post')

    # plt.xlim(xmax=2000, xmin=-250)
    # plt.ylim(ymin=0)
    ax.grid(linestyle="dashed", color='#eeeeee')
    ax.set_xlabel('Rank')
    ax.set_ylabel('Number of Images [%]')

    pt.info(">> Saving the graph...")
    save_fig(graph_filename)
