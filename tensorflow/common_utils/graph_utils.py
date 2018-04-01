import numpy as np
#import matplotlib as mpl
from common_utils import console
#mpl.use("pgf")
import matplotlib.pyplot as plt
import random
from matplotlib import colors as mcolors


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
            r"\usepackage[english]{babel}",
            r"\usepackage[utf8x]{inputenc}",  # use utf8 fonts becasue your computer can handle it :)
            r"\usepackage[T1]{fontenc}",  # plots will be generated using this preamble
        ]
    }
#mpl.rcParams.update(pgf_with_latex())


def new_fig(width, no_plots=1):
    plt.clf()
    fig = plt.figure(figsize=fig_size(width))

    plot_dim = no_plots * 100 + 11
    if no_plots % 2 == 0:
        plot_dim = 201 + no_plots / 2 * 10
    elif no_plots % 3 == 0:
        plot_dim = 301 + no_plots / 3 * 10

    axs = []
    for i in range(no_plots):
        ax = fig.add_subplot(plot_dim)
        axs.append(ax)
        plot_dim += 1
    # plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9)
    if len(axs) == 1:
        return fig, axs[0]
    return fig, axs


def save_fig(filename):
    plt.savefig('{}.pgf'.format(filename), bbox_inches='tight')
    plt.savefig('{}.pdf'.format(filename), bbox_inches='tight')


def plot_histogram(plots, bins, graph_filename, title, figure_size=2):
    pt = console.ProgressTracker()
    pt.info(">> Plotting a histogram...")

    fig, ax = new_fig(figure_size)

    ax.grid(linestyle="dashed", color='#eeeeee')
    ax.set_xlabel('Distance')
    ax.set_ylabel('Number of Images (normed)')

    for key in plots.keys():
        plot = plots[key]
        ax.hist(plot, bins=bins, label=key, normed=True)

    plt.title(title)
    plt.legend(loc='lower right')

    pt.info(">> Saving the graph...")
    save_fig(graph_filename)


def plot_discrete_histogram(plots, bins, graph_filename, title, figure_size=2):
    pt = console.ProgressTracker()
    pt.info(">> Plotting a histogram...")

    fig, axs = new_fig(figure_size, no_plots=len(plots))

    # fig.suptitle(title)

    for index, key in enumerate(sorted(plots.keys())):
        plot = plots[key]
        y = np.zeros(bins)

        for rank in plot:
            y[rank-1] += 1
        x = np.arange(1, bins + 1)

        axs[index].set_title("\\textsc{" + key + "}")
        axs[index].grid(linestyle="dashed", color='#eeeeee')

        y = y / np.sum(y)
        axs[index].bar(x, y, color='C9', label="Histogram")

        lmbda = len(plot) / np.sum(plot)
        pt.info("\t> " + key + " lambda: " + str(lmbda))
        # ax = np.linspace(np.min(x), np.max(x), 200)
        ay = lmbda * np.exp(-lmbda * x)
        axs[index].plot(x, ay, label="Exp $\\lambda e^{\\lambda x}$")

        smoothed = np.zeros(bins)
        for i in range(bins):
            for j in range(max(0, i-10), min(i+10, bins)):
                smoothed[i] += y[j]
            smoothed[i] /= min(i+10, bins) - max(0, i-10)

        axs[index].plot(x, smoothed, label="Smoothed")

        min_reached = smoothed[0]
        accumulated = 0.0
        for i in range(1, bins):
            if min_reached < smoothed[i]:
                accumulated += smoothed[i] - min_reached
                smoothed[i] = min_reached
            elif smoothed[i] + accumulated > min_reached:
                accumulated -= min_reached - smoothed[i]
                smoothed[i] = min_reached
            else:
                smoothed[i] += accumulated
                accumulated = 0
                min_reached = smoothed[i]

        smoothed /= np.sum(smoothed)

        axs[index].plot(x, smoothed, label="Smoothed Dec")

        axs[index].legend(loc='upper right')
        # axs[index].set_xlabel('Rank')
        # axs[index].set_ylabel('Number of Images [%]')

    pt.info(">> Saving the graph...")
    save_fig(graph_filename)


def plot_accumulative(plots, graph_filename, title, x_axis, y_axis, viewbox=None, figure_size=0.5):
    pt = console.ProgressTracker()
    pt.info(">> Plotting a graph...")

    fig, ax = new_fig(figure_size)

    for key in sorted(plots.keys()):
        plot = plots[key]
        plot.sort(key=lambda r: r if r is not None else 2147483648 - 1)
        x, y = [], []
        i = 0

        for rank in plot:
            if rank is None:
                break
            i += 1
            x.append(rank)
            y.append(i/len(plot)*100)

        ax.step(x, y, where='post', label=key)

    if viewbox is not None:
        plt.xlim(xmin=viewbox[0][0], xmax=viewbox[0][1])
        plt.ylim(ymin=viewbox[1][0], ymax=viewbox[1][1])

    if title is not None:
        plt.title(title)
    plt.legend(loc='lower right')

    ax.grid(linestyle="dashed", color='#eeeeee')
    ax.set_xlabel(x_axis)
    ax.set_ylabel(y_axis)

    pt.info(">> Saving the graph...")
    save_fig(graph_filename)


def plot_scatter(plots, centroids, graph_filename, figure_size=1):
    fig, ax = new_fig(figure_size)

    colors = [mcolors.to_rgba(color) for name, color in mcolors.CSS4_COLORS.items()]
    random.shuffle(colors)
    ncolors = []
    for c in colors:
        if not (c[0] > 0.8 and c[1] > 0.8 and c[2] > 0.8):
            ncolors.append(c)

    for i, color in zip(range(len(plots)), ncolors):
        ax.scatter(plots[i][:, 0], plots[i][:, 1], color=color, s=0.15, alpha=0.9)
        ax.scatter(centroids[i, 0], centroids[i, 1], marker='x', s=20, color=color, zorder=10)
        ax.text(centroids[i, 0], centroids[i, 1], str(i), size=6, zorder=20)

    plt.xticks(())
    plt.yticks(())

    save_fig(graph_filename)
