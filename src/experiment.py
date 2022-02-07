"""
A module holding Experiment class that represent entire dataset
 from a file along with basic operations on it.
"""
from collections import namedtuple

import os
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from scipy.stats import entropy

ColumnMeaning = namedtuple("ColumnMeaning", "description unit")

class Experiment:
    """
    A class that represent an experiment of entropy calculation
    from angles from the single file
    """
    def __init__(self, filepath: str):
        self.dataframe = pd.read_csv(filepath, sep=";", skipfooter=2, engine="python")
        self.chain = 'side chain' if 'sidechain' in filepath else 'main chain'
        self.columns = [
            ColumnMeaning("Time", "ps"),
            ColumnMeaning("Total energy of the system", "kJ/mol"),
            ColumnMeaning("Total bond energy", "kJ/mol"),
            ColumnMeaning("Total angle energy", "kJ/mol"),
            ColumnMeaning("Total dihedral energy", "kJ/mol"),
            ColumnMeaning("Total planar energy", "kJ/mol"),
            ColumnMeaning("Total Coulomb energy", "kJ/mol"),
            ColumnMeaning("Total Van der Waals energy", "kJ/mol"),
        ]
        if self.chain == 'main chain':
            angles = ["ϕ₁₄","ψ₁₄","ϕ₁₃","ψ₁₃"]
            for mer in range(23):
                for angle in angles:
                    self.columns.append(ColumnMeaning(f"{angle} mers {mer+1}, {mer+2}", "deg"))
            
        elif self.chain == 'side chain':
            angles = ["γ","ω","δ"]
            for angle in angles:
                for mer in range(23):
                    self.columns.append(ColumnMeaning(f"{angle} mers {mer+1}, {mer+2}", "deg"))

    def drop_first_observations(self):
        """
        Drops first observations so that only points after stabilisation are
        further considered
        """
        self.dataframe.drop(index=self.dataframe.index[0], axis=0, inplace=True)

    def plot_columns(self, ycol: int, plotname: str = None):
        """
        Plots one column vs another (time by default).
        Stores to pdf file if plot name is provided.
        """
        xcol = 0
        xname, xunit = self.columns[xcol]
        yname, yunit = self.columns[ycol]
        myxlab = f"{xname} [{xunit}]"
        myylab = f"{yname} [{yunit}]"
        mytitle = f"{self.chain} {xname} vs {yname}"

        y = self.dataframe.iloc[:, ycol]
        x = self.dataframe.iloc[:, xcol]
        y = correct_signs(y)

        plt.plot(x, y)
        plt.xlabel(myxlab)
        plt.ylabel(myylab)
        plt.title(mytitle)

        if plotname:
            plot_filepath = f"{plotname}series_{self.chain.replace(' ','')}_{ycol}.pdf"
            plt.savefig(plot_filepath)
            plt.clf()
        else:
            plt.show()

    def plot_histogram_2d(self, xcol: int, ycol: int, plotname: str = None):
        """
        Plots one column vs another 2D histogram
        """
        xname, xunit = self.columns[xcol]
        yname, yunit = self.columns[ycol]
        myxlab = f"{xname} [{xunit}]"
        myylab = f"{yname} [{yunit}]"
        mytitle = "{self.chain} Histogram 2D"
        y = self.dataframe.iloc[:, ycol]
        y = correct_signs(y)

        x = self.dataframe.iloc[:, xcol]
        x = correct_signs(x)

        plt.subplots()
        plt.hist2d(x, y, bins=10, cmap=plt.cm.Reds)
        plt.colorbar(format=mtick.FormatStrFormatter("%.1e"))
        plt.xlabel(myxlab)
        plt.ylabel(myylab)
        plt.title(mytitle)
        if plotname:
            plot_filepath = f"{plotname}hist2D_{self.chain.replace(' ','')}_{xcol}_{ycol}.pdf"
            plt.savefig(plot_filepath)
            plt.clf()
        else:
            plt.show()

    def get_entropy(self, xcol: int, ycol: int):
        """
        computes entropy from histogram of xcol vs. ycol
        """
        self.drop_first_observations()
        y = self.dataframe.iloc[:, ycol]
        y = correct_signs(y)
        x = self.dataframe.iloc[:, xcol]
        x = correct_signs(x)

        h = np.histogram2d(x, y, bins=10)
        h_vec = np.concatenate(h[0])
        h_norm = h_vec / sum(h_vec)
        # use molar gas constant R = 8.314
        return 8.314 * entropy(h_norm)


class SetOfExperiments:
    """
    this class represents a set of experiments of entropy calculation
     performed in a series of files for statistics
    """
    magic_numbers = {'analysis': 4,
                     'sidechain' : 1}

    def __init__(self, data_path: str, experiment_prefix: str, ion: str, chain: str, no_experiments: int = 12):
        self.partial_path = os.path.join(data_path, f"{experiment_prefix}_")
        self.ion = ion
        assert chain in ['analysis', 'sidechain'], f"Incorrect chain type: {chain}"
        self.chain = chain
        self.no_experiments = no_experiments
        self.magic_number = self.magic_numbers[self.chain]
        experiment_file_names = [f"{experiment_prefix}_{i+1}_{chain}_{ion}.tab" for i in range(no_experiments)]
        self.experiments = [Experiment(os.path.join(data_path, fp)) for fp in experiment_file_names]

    def hist_of_entropy(self, xcol: int, ycol: int, plotdir: str = None):
        """ compute histogram of entropy over realisations """
        entropies = [experiment.get_entropy(xcol, ycol) for experiment in self.experiments]

        if plotdir:
            xdesc = self.experiments[0].columns[xcol].description
            ydesc = self.experiments[0].columns[ycol].description
            plotFile = f"{plotdir}hist{xdesc}_{ydesc}.pdf"
            mytitle = f"{self.chain} {self.ion}"
            myxlabel = f"entropy {xdesc} vs. {ydesc}"
            myylabel = "frequency"

            plt.subplots()
            plt.hist(entropies, bins=5)
            plt.title(mytitle)
            plt.xlabel(myxlabel)
            plt.ylabel(myylabel)

            plt.savefig(plotFile)
            plt.clf()
        return entropies

    def entropy_distribution_percentiles(self, xcol: int, ycol: int, plotdir: str, no_mers: int = 23):
        """  compute percentiles of the histogram of entropies """
        first_mers = list(range(1, no_mers+1))

        median_entropy = []
        entropy_perc5 = []
        entropy_perc95 = []

        for mer in range(no_mers):
            entropies = np.array(self.hist_of_entropy(xcol + self.magic_number * mer, ycol + self.magic_number * mer))
            median_entropy.append(np.median(entropies))
            entropy_perc5.append(np.percentile(entropies, 5))
            entropy_perc95.append(np.percentile(entropies, 95))

        xdesc = self.experiments[0].columns[xcol].description
        ydesc = self.experiments[0].columns[ycol].description

        mytitle = f"{self.chain}, ion {self.ion}"
        myylabel = f"entropy  {xdesc} vs. {ydesc}"
        myxlabel = "number of first mer"

        plt.plot(first_mers, median_entropy, "o--", color="red", label="median")
        plt.plot(first_mers, entropy_perc5, ":", color="red", label="5 and 95 perc.")
        plt.plot(first_mers, entropy_perc95, ":", color="red", label=None)
        plt.legend()
        plt.title(mytitle)
        plt.xlabel(myxlabel)
        plt.ylabel(myylabel)
        plot_filepath = os.path.join(plotdir, f"entropy_{self.chain}_{self.ion}_{xdesc}_{ydesc}.pdf")
        plt.savefig(plot_filepath)
        plt.clf()

        return median_entropy

    def entropy_distribution_realisations(self, xcol: int, ycol: int, plotdir: str, no_mers: int = 23):
        """  compute percentiles of the histogram of entropies """
        no_struct = 12
        first_mers = list(range(1, no_mers+1))
        print("highest first mer", first_mers[-1])
        entropies = [[0.0 for i in range(no_struct)] for _ in range(no_mers)]

        for mer in range(no_mers):
            entropies[mer] = np.array(self.hist_of_entropy(xcol + self.magic_number * mer, ycol + self.magic_number * mer))

        xdesc = self.experiments[0].columns[xcol].description
        ydesc = self.experiments[0].columns[ycol].description

        mytitle = f"{self.chain}, ion {self.ion}"
        myylabel = f"entropy  {xdesc} vs. {ydesc}"
        myxlabel = "number of first mer"

        for j in range(no_struct):
            color = 5 / 6 * (1 - j / no_struct) * np.array((1, 1, 1))
            e = [entropies[i][j] for i in range(no_mers)]
            plt.plot(first_mers, e, label=f"{j+1}", color=color)

        plt.legend()
        plt.title(mytitle)
        plt.xlabel(myxlabel)
        plt.ylabel(myylabel)
        plot_filepath = os.path.join(plotdir, f"entropy_reals_{self.chain}_{self.ion}_{xdesc}_{ydesc}.pdf")
        plt.savefig(plot_filepath)
        plt.clf()

def correct_signs(series, thres: float = 0.5):
    """ if the sign of the angle is artificially reversed,
    we reverse it back"""
    series_corrected = np.array(series)

    for i in range(len(series_corrected) - 1):
        if np.abs(series_corrected[i] + series_corrected[i + 1]) < thres * np.abs(series_corrected[i + 1]):
            series_corrected[i + 1:] *= -1
    return series_corrected
