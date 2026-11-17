import unittest

from fastapi.testclient import TestClient

from matching_system.api import app
from matching_system.nlp_retrieval import TextReport
from matching_system.pipeline import MatchingPipeline


class Day3IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_report_to_staff_review(self):
        response = self.client.post("/preview/matches", json={
            "item_name": "Metal water bottle",
            "description": "Blue bottle with a scratched lid",
            "category_id": "metal_water_bottle",
            "location_id": "msb",
            "event_date": "2026-11-10",
            "limit": 3,
        })
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["mode"], "synthetic_preview")
        self.assertEqual(body["status"], "possible_matches")
        self.assertLessEqual(len(body["matches"]), 3)
        first = body["matches"][0]
        self.assertEqual(first["found_report_id"], "demo-found-metal")
        self.assertIn("CATEGORY_AGREEMENT", first["reason_codes"])
        self.assertEqual(first["workflow"]["action"], "review_conflicts")
        self.assertFalse(first["workflow"]["ownership_approved"])
        self.assertFalse(first["workflow"]["release_authorized"])
        self.assertNotIn("Blue metal bottle with scratched lid", str(body))
        plastic = next(row for row in body["matches"] if row["found_report_id"] == "demo-found-plastic")
        self.assertIn("CATEGORY_CONFLICT", plastic["reason_codes"])

    def test_no_lexical_candidate_and_redacted_validation(self):
        response = self.client.post("/preview/matches", json={
            "item_name": "Telescope", "description": "Violet telescope SYNTHETIC-X999",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "no_lexical_candidates")
        rejected = self.client.post("/preview/matches", json={
            "item_name": "Bottle", "description": "Blue bottle", "id_number": "00012345",
        })
        self.assertEqual(rejected.status_code, 422)
        self.assertNotIn("00012345", rejected.text)
        invalid_date = self.client.post("/preview/matches", json={
            "item_name": "Bottle", "description": "Blue bottle", "event_date": "2026-02-30",
        })
        self.assertEqual(invalid_date.status_code, 422)

    def test_inventory_refresh_changes_candidate_lookup(self):
        lost = TextReport("l1", "lost", "blue bottle")
        pipeline = MatchingPipeline([TextReport("f1", "found", "blue bottle")])
        self.assertEqual(pipeline.recommend(lost)["matches"][0]["found_report_id"], "f1")
        pipeline.replace_inventory([TextReport("f2", "found", "blue bottle")])
        self.assertEqual(pipeline.recommend(lost)["matches"][0]["found_report_id"], "f2")


if __name__ == "__main__":
    unittest.main()
