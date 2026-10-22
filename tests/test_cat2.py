import csv
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from matching_system.data_loader import load_reports
from matching_system.feature_builder import FEATURE_NAMES, pair_features
from matching_system.ml_model import run_experiment
from scripts.build_modelling_pairs import ROOT, build
from scripts.split_campus_data import split


class Cat2Tests(unittest.TestCase):
    def test_missing_attribute_is_not_a_conflict(self):
        build()
        reports = {row.report_id: row for row in load_reports(ROOT / "data/processed/synthetic_campus_reports.csv")}
        lost = replace(reports["lost-001"], brand="")
        found = replace(reports["found-001"], brand="Example")
        features = pair_features(lost, found)
        self.assertEqual((features["brand_match"], features["brand_conflict"]), (0, 0))
        self.assertEqual(set(features), set(FEATURE_NAMES))

    def test_modelling_pairs_keep_original_labels_and_binary_mapping(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "pairs.csv"
            result = build(path)
            with path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(result["rows"], 32)
        self.assertEqual({label: {row["target"] for row in rows if row["original_label"] == label}
                          for label in ("match", "plausible", "non_match")},
                         {"match": {"1"}, "plausible": {"0"}, "non_match": {"0"}})
        self.assertEqual(len({(row["lost_report_id"], row["found_report_id"]) for row in rows}), 32)

    def test_model_uses_grouped_split_and_writes_measured_results(self):
        build()
        split()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            result = run_experiment(ROOT / "data/processed/modelling_pairs.csv",
                                    ROOT / "data/processed/campus_split.json", Path(directory))
            saved = json.loads((Path(directory) / "validation_metrics.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["held_out_test"], result["held_out_test"])
        self.assertEqual(result["split"]["development_pairs"] + result["split"]["test_pairs"], 32)
        self.assertTrue(result["grouped_cv"])
        self.assertEqual(sum(sum(row) for row in result["held_out_test"]["confusion_matrix"]), 8)


if __name__ == "__main__":
    unittest.main()
