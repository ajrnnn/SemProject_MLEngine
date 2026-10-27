"""Prepare campus pairs, train Logistic Regression, and save measured results."""

from matching_system.ml_model import run_experiment
from scripts.build_modelling_pairs import ROOT, build
from scripts.split_campus_data import split


def main():
    pair_summary = build()
    split()
    result = run_experiment(ROOT / "data/processed/modelling_pairs.csv",
                            ROOT / "data/processed/campus_split.json", ROOT / "results/ml")
    test = result["held_out_test"]
    print(f"Prepared {pair_summary['rows']} labelled report pairs.")
    print(f"Development: {result['split']['development_pairs']} pairs; "
          f"held-out test: {result['split']['test_pairs']} pairs.")
    print(f"Held-out precision: {test['precision']:.2f}; "
          f"recall: {test['recall']:.2f}; F1: {test['f1']:.2f}")
    print("Detailed results: results/ml/validation_metrics.json")


if __name__ == "__main__":
    main()
