"""
Reading module that prints some basic statistical information about analysed
dataset.
Plots energy vs time in .png in /plots directory.
As first data points are considered artifacts they are dropped.
If more than one is dropped warning is displayed.
"""
import argparse
import os
import itertools

from collections import namedtuple
from experiment import Experiment, SetOfExperiments

plotDirectory = "plots"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Reads tabular data for molecular dynamics compute entropy"
    )

    parser.add_argument(
        "--datafolder",
        type=str,
        help="path to directory for folder with realisations",
        default="data",
    )

    parser.add_argument(
        "--plotdir", type=str, help="folder plots are saved", default="pics"
    )
    parser.add_argument(
        '--ions', nargs='+', type=str, help="Ions to be considered", default=["Ca", "Mg", "Na"]
    )
    parser.add_argument(
        '--modes', nargs='+', type=str, help="'analysis' and 'sidechain' allowed'", default=["analysis", "sidechain"]
    )
    parser.add_argument(
        "--complex", type=str, help="Complex chosen", default="Albumin+HA"
    )

    args = parser.parse_args()

    startingPoints = {

        'analysis' : [ ('ϕ₁₄ mers 1, 2', 'ψ₁₄ mers 1, 2'),
                       ('ϕ₁₃ mers 1, 2', 'ψ₁₃ mers 1, 2'),
                       ('ϕ₁₄ mers 1, 2', 'ϕ₁₃ mers 1, 2')],

        'sidechain' : [('γ mers 1, 2', 'ω mers 1, 2'),
                       ('γ mers 1, 2', 'δ mers 1, 2'),
                       ('ω mers 1, 2', 'δ mers 1, 2')]
    }

    numRealisations = 2 
    
    print(f"{args.complex=}")
    print(f"{args.ions=}")
    print(f"{args.modes=}")

    for myMode in args.modes:
        for ion in args.ions:
            for i in range(1,numRealisations+1):
                file_path = os.path.join(args.datafolder, f"{args.complex}_{i}_{myMode}_{ion}.tab")

                myExperiment = Experiment(file_path)
                myExperiment.drop_first_observations()
                myExperiment.plot_columns(8, os.path.join(args.plotdir, f"realisation{i}_{ion}_"))
                myExperiment.plot_histogram_2d(startingPoints[myMode][0][0], startingPoints[myMode][0][1], os.path.join(args.plotdir, f"realisation{i}_{ion}_"))

    for myMode in args.modes:
        for ion in args.ions:
            mySetOfExperiments = SetOfExperiments(args.datafolder, args.complex, ion, myMode)

            angles = mySetOfExperiments.experiments[0].angles

            for angle1,angle2 in itertools.combinations(angles,2):
                print(f"{angle1=} {angle2=}")
                mySetOfExperiments.entropy_distribution_percentiles(angle1, angle2, args.plotdir)
                mySetOfExperiments.entropy_distribution_realisations(angle1, angle2, args.plotdir)

            for p in startingPoints[myMode]:
                mySetOfExperiments.hist_of_entropy(p[0], p[1], args.plotdir)
