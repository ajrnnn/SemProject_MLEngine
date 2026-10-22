"""Regenerate the CAT 2 pair table, grouped split and measured model outputs."""

import json

from matching_system.ml_model import run_experiment
from scripts.build_modelling_pairs import ROOT, build
from scripts.split_campus_data import split


def main():
    print(build())
    split()
    result = run_experiment(ROOT / "data/processed/modelling_pairs.csv",
                            ROOT / "data/processed/campus_split.json", ROOT / "results/ml")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
