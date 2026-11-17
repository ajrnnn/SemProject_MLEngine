import unittest

from matching_system.matching_agent import (
    CandidateRecommendation,
    FactStatus,
    assess_candidate,
)
from matching_system.nlp_retrieval import TextReport
from matching_system.staff_workflow_agent import (
    WorkflowAction,
    recommend_staff_workflow,
)


class MatchingAgentTests(unittest.TestCase):
    def make_reports(self, **overrides):
        lost_values = {
            "report_id": "l1",
            "report_type": "lost",
            "description": "blue bottle",
            "category_id": "bottle",
            "location_id": "library",
            "event_date": "2026-11-16",
        }
        found_values = {
            "report_id": "f1",
            "report_type": "found",
            "description": "blue bottle",
            "category_id": "bottle",
            "location_id": "library",
            "event_date": "2026-11-16",
        }
        lost_overrides = overrides.get("lost", {})
        found_overrides = overrides.get("found", {})
        lost_values.update(lost_overrides)
        found_values.update(found_overrides)
        return TextReport(**lost_values), TextReport(**found_values)

    def test_agreeing_facts_produce_review_recommendation(self):
        lost, found = self.make_reports()
        result = assess_candidate(lost, found, 0.82)

        self.assertEqual(result.evidence_state, FactStatus.AGREEMENT)
        self.assertEqual(
            result.candidate_recommendation,
            CandidateRecommendation.STAFF_REVIEW,
        )
        self.assertEqual(result.text_similarity, 0.82)
        self.assertEqual(
            result.to_dict()["rule_ids"],
            ["MA-R001", "MA-R004", "MA-R007", "MA-R010"],
        )

    def test_category_conflict_excludes_candidate(self):
        lost, found = self.make_reports(found={"category_id": "wallet"})

        result = assess_candidate(lost, found, 0.99)

        self.assertEqual(result.evidence_state, FactStatus.CONFLICT)
        self.assertEqual(
            result.candidate_recommendation,
            CandidateRecommendation.EXCLUDE_CANDIDATE,
        )
        self.assertIn("CATEGORY_CONFLICT", result.reason_codes)

    def test_location_difference_alone_does_not_exclude_candidate(self):
        lost, found = self.make_reports(found={"location_id": "cafeteria"})

        result = assess_candidate(lost, found, 0.4)
        location = result.facts[1]

        self.assertEqual(location.status, FactStatus.CONFLICT)
        self.assertEqual(
            location.reason_code,
            "LOCATION_DIFFERENCE_NON_DISPOSITIVE",
        )
        self.assertEqual(
            result.candidate_recommendation,
            CandidateRecommendation.STAFF_REVIEW,
        )

    def test_missing_fields_are_unknown_not_conflicts(self):
        lost, found = self.make_reports(
            lost={"category_id": None, "location_id": ""},
            found={"category_id": "bottle", "location_id": None},
        )

        result = assess_candidate(lost, found, 0.0)

        self.assertEqual(result.facts[0].status, FactStatus.UNKNOWN)
        self.assertEqual(result.facts[1].status, FactStatus.UNKNOWN)
        self.assertEqual(
            result.candidate_recommendation,
            CandidateRecommendation.STAFF_REVIEW,
        )

    def test_invalid_report_order_and_similarity_are_rejected(self):
        lost, found = self.make_reports()

        with self.assertRaisesRegex(ValueError, "first report"):
            assess_candidate(found, lost, 0.5)
        with self.assertRaisesRegex(ValueError, "between 0 and 1"):
            assess_candidate(lost, found, 1.1)


class StaffWorkflowAgentTests(unittest.TestCase):
    def test_workflow_requires_review_and_never_approves_or_releases(self):
        lost = TextReport("l1", "lost", "blue bottle", category_id=None)
        found = TextReport("f1", "found", "blue bottle", category_id="bottle")
        assessment = assess_candidate(lost, found, 0.7)

        recommendation = recommend_staff_workflow(assessment)
        output = recommendation.to_dict()

        self.assertEqual(recommendation.action, WorkflowAction.STAFF_REVIEW)
        self.assertFalse(output["ownership_approved"])
        self.assertFalse(output["release_authorized"])
        self.assertIn("STAFF_REVIEW_REQUIRED", output["reason_codes"])


if __name__ == "__main__":
    unittest.main()
