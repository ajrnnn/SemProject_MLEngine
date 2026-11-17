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
        self.assertIn("category agrees", first["explanation"])
        self.assertIn("location differs", first["explanation"])
        self.assertIn("Staff should review", first["explanation"])
        self.assertIn("rule_trace", first)
        self.assertIn("rule_ids", first)

    def test_candidate_explanations_cover_agreement_conflict_and_missing_details(self):
        lost = TextReport(
            "l1",
            "lost",
            "blue bottle",
            category_id="bottle",
            location_id="library",
            event_date="2026-11-16",
        )
        pipeline = MatchingPipeline([
            TextReport(
                "f-agree",
                "found",
                "blue bottle",
                category_id="bottle",
                location_id="library",
                event_date="2026-11-17",
            ),
            TextReport(
                "f-conflict",
                "found",
                "blue bottle",
                category_id="wallet",
                location_id="cafeteria",
                event_date="2026-11-15",
            ),
            TextReport(
                "f-missing",
                "found",
                "blue bottle",
                category_id=None,
                location_id="library",
                event_date=None,
            ),
        ])

        matches = {
            match["found_report_id"]: match
            for match in pipeline.recommend(lost)["matches"]
        }

        self.assertIn("category agrees", matches["f-agree"]["explanation"])
        self.assertIn("Staff should review this possible match", matches["f-agree"]["explanation"])
        self.assertIn("category differs", matches["f-conflict"]["explanation"])
        self.assertIn("location differs", matches["f-conflict"]["explanation"])
        self.assertIn("review the conflicting details", matches["f-conflict"]["explanation"])
        self.assertIn("category is missing or unknown", matches["f-missing"]["explanation"])
        self.assertIn("event date is missing or unknown", matches["f-missing"]["explanation"])
        self.assertIn("request or verify additional details", matches["f-missing"]["explanation"])

    def test_no_lexical_candidate_and_redacted_validation(self):
        response = self.client.post("/preview/matches", json={
            "item_name": "Telescope", "description": "Violet telescope SYNTHETIC-X999",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "no_lexical_candidates")
        rejected = self.client.post("/preview/matches", json={
            "item_name": "Bottle",
            "description": "Blue bottle",
            "id_number": "00012345",
            "email": "alice@example.com",
            "student_id": "SYNTHETIC-CONTACT-999",
        })
        self.assertEqual(rejected.status_code, 422)
        self.assertNotIn("00012345", rejected.text)
        self.assertNotIn("alice@example.com", rejected.text)
        self.assertNotIn("SYNTHETIC-CONTACT-999", rejected.text)
        invalid_date = self.client.post("/preview/matches", json={
            "item_name": "Bottle", "description": "Blue bottle", "event_date": "2026-02-30",
            "phone_number": "+15551234567",
        })
        self.assertEqual(invalid_date.status_code, 422)
        self.assertNotIn("+15551234567", invalid_date.text)

    def test_obvious_private_data_in_free_text_is_rejected_without_echo(self):
        private_values = (
            "alice.person@example.com",
            "+1 (555) 123-4567",
            "student_id SYNTHETIC-ID-1234",
            "national ID: 12345678",
        )
        for value in private_values:
            with self.subTest(value=value):
                response = self.client.post("/preview/matches", json={
                    "item_name": "Bottle",
                    "description": f"Blue bottle {value}",
                })
                self.assertEqual(response.status_code, 422)
                self.assertEqual(
                    response.json(),
                    {"detail": "Invalid general-item preview request"},
                )
                self.assertNotIn(value, response.text)

    def test_calendar_date_in_description_is_not_treated_as_contact_data(self):
        response = self.client.post("/preview/matches", json={
            "item_name": "Metal water bottle",
            "description": "Blue bottle found on 2026-11-11",
        })

        self.assertEqual(response.status_code, 200)

    def test_explanation_does_not_repeat_contact_or_private_identifiers(self):
        private_values = (
            "alice@example.com",
            "+15551234567",
            "SYNTHETIC-ID-1234",
        )
        lost = TextReport(
            "l1",
            "lost",
            "Blue bottle with scratched lid " + " ".join(private_values),
            item_name="Metal water bottle",
            category_id="metal_water_bottle",
            location_id="msb",
            event_date="2026-11-10",
        )
        pipeline = MatchingPipeline([
            TextReport(
                "f1",
                "found",
                "Blue metal bottle with scratched lid",
                item_name="Metal water bottle",
                category_id="metal_water_bottle",
                location_id="cafeteria",
                event_date="2026-11-11",
            )
        ])
        output = pipeline.recommend(lost)

        for private_value in (
            *private_values,
        ):
            self.assertNotIn(private_value, str(output))

    def test_inventory_refresh_changes_candidate_lookup(self):
        lost = TextReport("l1", "lost", "blue bottle")
        pipeline = MatchingPipeline([TextReport("f1", "found", "blue bottle")])
        self.assertEqual(pipeline.recommend(lost)["matches"][0]["found_report_id"], "f1")
        pipeline.replace_inventory([TextReport("f2", "found", "blue bottle")])
        self.assertEqual(pipeline.recommend(lost)["matches"][0]["found_report_id"], "f2")


if __name__ == "__main__":
    unittest.main()
