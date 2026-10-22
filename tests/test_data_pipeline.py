import csv
import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from matching_system.data_loader import load_reports
from scripts.prepare_campus_data import ROOT, SOURCE as CAMPUS_SOURCE, prepare as prepare_campus
from scripts.prepare_delhi_data import COLUMNS, prepare as prepare_delhi
from scripts.split_campus_data import split


class DataPipelineTests(unittest.TestCase):
    def test_campus_correction_preserves_raw_and_rows(self):
        before = hashlib.sha256(CAMPUS_SOURCE.read_bytes()).digest()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            output = Path(directory) / "campus.csv"
            report = prepare_campus(output=output)
            rows = load_reports(output)
        self.assertEqual(before, hashlib.sha256(CAMPUS_SOURCE.read_bytes()).digest())
        self.assertEqual(len(rows), 46)
        self.assertEqual(len(report["repaired_ids"]), 6)
        umbrella = next(row for row in rows if row.report_id == "found-015")
        self.assertEqual(umbrella.colour, "black")
        self.assertEqual(umbrella.material, "")

    def test_delhi_schema_missing_and_dates(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root = Path(directory)
            source, output, report_path = (root / name for name in ("raw.csv", "processed.csv", "report.json"))
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=COLUMNS)
                writer.writeheader()
                writer.writerow(dict(zip(COLUMNS, ["  BAG  ", "", "", "A  B", "15/12/2021", "11:35:00"])))
            raw = source.read_bytes()
            result = prepare_delhi(source, output, report_path)
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(result["original_rows"], result["final_rows"])
            self.assertEqual(result["missing_values"], {"description": 1, "item_quantity": 1})
            self.assertEqual(result["parsing_failures"], {})
            with output.open(encoding="utf-8", newline="") as handle:
                self.assertEqual(next(csv.DictReader(handle))["receiving_date_iso"], "2021-12-15")
            self.assertEqual(json.loads(report_path.read_text(encoding="utf-8"))["source_sha256"], hashlib.sha256(raw).hexdigest())

    def test_grouped_split_has_no_leakage(self):
        manifest = split()
        dev = manifest["splits"]["development"]
        test = manifest["splits"]["test"]
        self.assertEqual((len(dev["lost_ids"]), len(test["lost_ids"])), (10, 4))
        self.assertFalse(set(dev["found_ids"]) & set(test["found_ids"]))
        self.assertEqual(dev["pair_count"] + test["pair_count"], 32)

    def test_api_recommendations_require_review_and_inventory_is_minimal(self):
        from matching_system.api import MatchRequest, create_report_placeholder, find_matches, health, list_reports

        self.assertEqual(health(), {"status": "ok"})
        inventory = list_reports()
        self.assertEqual(len(inventory), 46)
        self.assertEqual(set(inventory[0]), {"report_id", "report_type", "category", "status"})
        matches = find_matches(MatchRequest(lost_report_id="lost-001", min_score=0))
        self.assertTrue(all(item["requires_human_verification"] for item in matches["matches"]))
        post = create_report_placeholder({"phone_number": "private", "student_id": "private"})
        self.assertNotIn("private", str(post))

    def test_image_similarity_is_supporting_evidence_only(self):
        from matching_system.image_matching import cosine_similarity
        from matching_system.matcher import score_pair

        self.assertAlmostEqual(cosine_similarity((1.0, 0.0), (1.0, 0.0)), 1.0)
        with self.assertRaises(ValueError):
            cosine_similarity((0.0, 0.0), (1.0, 0.0))
        rows = {row.report_id: row for row in load_reports(ROOT / "data/processed/synthetic_campus_reports.csv")}
        lost = replace(rows["lost-004"], image_reference="lost.jpg")
        good = replace(rows["found-010"], image_reference="good.jpg")
        conflict = replace(rows["found-012"], image_reference="conflict.jpg")
        vectors = {name: (1.0, 0.0) for name in ("lost.jpg", "good.jpg", "conflict.jpg")}
        self.assertGreater(score_pair(lost, good, vectors).score, score_pair(lost, good).score)
        self.assertEqual(score_pair(lost, conflict, vectors).score, score_pair(lost, conflict).score)


if __name__ == "__main__":
    unittest.main()
