import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_delhi_experiment import validate


class DelhiValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)
        self.pairs_path = self.directory / "pairs.csv"
        self.split_path = self.directory / "split.json"
        self.pairs = [
            {"lost_report_id": "lost-1", "found_report_id": "found-1",
             "match": "1", "label_basis": "constructed_positive"},
            {"lost_report_id": "lost-1", "found_report_id": "found-2",
             "match": "0", "label_basis": "assumed_same_name_negative"},
            {"lost_report_id": "lost-1", "found_report_id": "found-3",
             "match": "0", "label_basis": "assumed_other_name_negative"},
            {"lost_report_id": "lost-2", "found_report_id": "found-4",
             "match": "1", "label_basis": "constructed_positive"},
            {"lost_report_id": "lost-2", "found_report_id": "found-5",
             "match": "0", "label_basis": "assumed_same_name_negative"},
            {"lost_report_id": "lost-2", "found_report_id": "found-6",
             "match": "0", "label_basis": "assumed_other_name_negative"},
        ]
        self.split = {
            "splits": {
                "development": {
                    "lost_ids": ["lost-1"],
                    "found_ids": ["found-1", "found-2", "found-3"],
                    "pair_count": 3,
                },
                "test": {
                    "lost_ids": ["lost-2"],
                    "found_ids": ["found-4", "found-5", "found-6"],
                    "pair_count": 3,
                },
            }
        }
        self.write_fixtures()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write_fixtures(self):
        with self.pairs_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.pairs[0].keys())
            writer.writeheader()
            writer.writerows(self.pairs)
        self.split_path.write_text(json.dumps(self.split), encoding="utf-8")

    def test_accepts_valid_pairs_and_split(self):
        self.assertEqual(validate(self.pairs_path, self.split_path), {
            "lost_claims": 2, "pairs": 6, "development_pairs": 3, "test_pairs": 3,
        })

    def test_rejects_missing_candidate_and_wrong_label_mix(self):
        self.pairs.pop()
        self.pairs[-1]["match"] = "1"
        self.pairs[-1]["label_basis"] = "constructed_positive"
        self.split["splits"]["test"]["found_ids"].pop()
        self.split["splits"]["test"]["pair_count"] = 2
        self.write_fixtures()
        with self.assertRaisesRegex(ValueError, "exactly 3 candidate pairs"):
            validate(self.pairs_path, self.split_path)

    def test_rejects_reused_found_id(self):
        self.pairs[-1]["found_report_id"] = "found-1"
        self.write_fixtures()
        with self.assertRaisesRegex(ValueError, "found ID is reused"):
            validate(self.pairs_path, self.split_path)

    def test_rejects_ids_that_cross_splits(self):
        self.split["splits"]["test"]["lost_ids"].append("lost-1")
        self.write_fixtures()
        with self.assertRaisesRegex(ValueError, "appear in both development and test"):
            validate(self.pairs_path, self.split_path)

    def test_rejects_found_ids_that_cross_splits(self):
        self.split["splits"]["test"]["found_ids"].append("found-1")
        self.write_fixtures()
        with self.assertRaisesRegex(ValueError, "found IDs appear in both development and test"):
            validate(self.pairs_path, self.split_path)

    def test_rejects_incorrect_label_basis(self):
        self.pairs[0]["label_basis"] = "assumed_other_name_negative"
        self.write_fixtures()
        with self.assertRaisesRegex(ValueError, "positive pair must have label_basis"):
            validate(self.pairs_path, self.split_path)

    def test_rejects_pair_count_mismatch(self):
        self.split["splits"]["test"]["pair_count"] = 4
        self.write_fixtures()
        with self.assertRaisesRegex(ValueError, "test pair_count"):
            validate(self.pairs_path, self.split_path)


if __name__ == "__main__":
    unittest.main()
