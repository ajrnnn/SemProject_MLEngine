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

    def test_word_order_and_similar_item_distractor(self):
        lost = TextReport("l1", "lost", "scratched lid on a blue metal bottle")
        found = [
            TextReport("plastic", "found", "blue plastic bottle with scratched lid"),
            TextReport("metal", "found", "blue metal bottle; lid scratched"),
        ]
        ranker = TfidfRanker(found)
        ranked = ranker.rank(lost)
        self.assertEqual([row["found_report_id"] for row in ranked], ["metal", "plastic"])
        self.assertTrue(all(0 < row["text_similarity"] <= 1 for row in ranked))
        self.assertLess(ranked[0]["text_similarity"], 1)
        self.assertEqual(ranker.rank(lost, min_similarity=(ranked[0]["text_similarity"] + 1) / 2), [])

    def test_inventory_replacement_and_cutoff(self):
        query = TextReport("l1", "lost", "violet telescope")
        ranker = TfidfRanker([TextReport("f1", "found", "blue backpack")])
        self.assertEqual(ranker.rank(query), [])
        ranker.replace_inventory([TextReport("f2", "found", "violet telescope")])
        self.assertEqual(ranker.rank(query)[0]["found_report_id"], "f2")
        with self.assertRaisesRegex(ValueError, "found reports only"):
            ranker.replace_inventory([query])
        self.assertEqual(ranker.rank(query)[0]["found_report_id"], "f2")
        ranker.replace_inventory([])
        self.assertEqual(ranker.rank(query), [])
        with self.assertRaisesRegex(ValueError, "between zero and one"):
            ranker.rank(query, min_similarity=1.1)
        with self.assertRaisesRegex(ValueError, "between one and five"):
            ranker.rank(query, limit=6)

    def test_top_five_limit_and_stable_ties(self):
        found = [TextReport(f"f{i}", "found", "black notebook") for i in range(7, 0, -1)]
        ranked = TfidfRanker(found).rank(TextReport("l1", "lost", "black notebook"))
        self.assertEqual([row["found_report_id"] for row in ranked], ["f1", "f2", "f3", "f4", "f5"])


if __name__ == "__main__":
    unittest.main()
