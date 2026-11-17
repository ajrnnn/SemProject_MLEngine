import csv
import tempfile
import unittest
from pathlib import Path

from matching_system.nlp_retrieval import (
    TextReport, TfidfRanker, load_text_reports_csv, normalize_report_text,
)


class NlpRetrievalTests(unittest.TestCase):
    def test_normalization_and_ranking(self):
        self.assertEqual(normalize_report_text("  BLUE-Case!!  "), "blue case")
        found = [
            TextReport("f2", "found", "red notebook", "Book"),
            TextReport("f1", "found", "blue case with scratched lid", "Bottle"),
        ]
        ranker = TfidfRanker(found)
        query = TextReport("l1", "lost", "scratched blue lid", "Bottle")
        self.assertEqual(ranker.rank(query)[0]["found_report_id"], "f1")
        self.assertEqual(ranker.rank(TextReport("l2", "lost", "violin bow")), [])
        self.assertEqual(TfidfRanker([]).rank(query), [])

    def test_explicit_csv_mapping_and_id_separation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reports.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["key", "kind", "details", "name", "id_number"])
                writer.writeheader()
                writer.writerow({"key": "f1", "kind": "found", "details": "blue bottle", "name": "Bottle", "id_number": "000123"})
            mapping = {"report_id": "key", "report_type": "kind", "description": "details", "item_name": "name"}
            reports = load_text_reports_csv(path, mapping)
            self.assertEqual(reports[0].item_name, "Bottle")
            self.assertNotIn("000123", repr(reports))
            with self.assertRaisesRegex(ValueError, "Private ID"):
                load_text_reports_csv(path, {"description": "id_number"})


if __name__ == "__main__":
    unittest.main()
