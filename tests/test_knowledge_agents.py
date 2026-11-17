import unittest

from matching_system.matching_agent import (
    CandidateRecommendation,
    FactStatus,
    RULE_REASON_CODES as MATCH_RULE_REASON_CODES,
    assess_candidate,
)
from matching_system.nlp_retrieval import TextReport
from matching_system.staff_workflow_agent import (
    RULE_REASON_CODES as WORKFLOW_RULE_REASON_CODES,
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

    def test_category_conflict_requires_review(self):
        lost, found = self.make_reports(found={"category_id": "wallet"})

        result = assess_candidate(lost, found, 0.99)

        self.assertEqual(result.evidence_state, FactStatus.CONFLICT)
        self.assertEqual(
            result.candidate_recommendation,
            CandidateRecommendation.STAFF_REVIEW,
        )
        self.assertIn("CATEGORY_CONFLICT", result.reason_codes)

    def test_broad_category_is_ambiguous_evidence(self):
        lost, found = self.make_reports(
            lost={"category_id": "Accessories"},
            found={"category_id": "accessories"},
        )

        result = assess_candidate(lost, found, 0.99)
        category = result.facts[0]
        category_trace = result.rule_trace[0]

        self.assertEqual(category.status, FactStatus.AMBIGUOUS)
        self.assertEqual(category.reason_code, "CATEGORY_AMBIGUOUS")
        self.assertEqual(category_trace.rule_id, "MA-R011")
        self.assertEqual(category_trace.reason_code, category.reason_code)
        self.assertEqual(result.evidence_state, FactStatus.AMBIGUOUS)
        self.assertEqual(
            result.candidate_recommendation,
            CandidateRecommendation.STAFF_REVIEW,
        )

    def test_found_after_loss_is_compatible_and_earlier_find_is_flagged(self):
        lost, later = self.make_reports(found={"event_date": "2026-11-17"})
        self.assertEqual(assess_candidate(lost, later, 0.5).facts[2].status, FactStatus.AGREEMENT)
        _, earlier = self.make_reports(found={"event_date": "2026-11-15"})
        self.assertEqual(assess_candidate(lost, earlier, 0.5).facts[2].status, FactStatus.CONFLICT)

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

    def test_cross_location_candidate_remains_available_to_staff(self):
        lost, found = self.make_reports(found={"location_id": "north-campus"})

        result = assess_candidate(lost, found, 0.83)
        output = result.to_dict()

        self.assertEqual(output["candidate_recommendation"], "staff_review")
        self.assertEqual(output["facts"][1]["status"], "conflict")
        self.assertEqual(output["facts"][1]["reason_code"], "LOCATION_DIFFERENCE_NON_DISPOSITIVE")

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

    def test_every_matching_rule_and_reason_is_emitted_as_a_trace_pair(self):
        scenarios = [
            self.make_reports(),
            self.make_reports(
                lost={"category_id": None, "location_id": None, "event_date": None},
                found={"category_id": None, "location_id": None, "event_date": None},
            ),
            self.make_reports(
                found={
                    "category_id": "wallet",
                    "location_id": "cafeteria",
                    "event_date": "2026-11-15",
                }
            ),
            self.make_reports(
                lost={"category_id": "Accessories"},
                found={"category_id": "wallet"},
            ),
        ]
        seen_rules = set()

        for lost, found in scenarios:
            result = assess_candidate(lost, found, 0.5)
            output = result.to_dict()
            trace = output["rule_trace"]
            self.assertEqual(output["rule_ids"], [item["rule_id"] for item in trace])
            self.assertEqual(output["reason_codes"], [item["reason_code"] for item in trace])
            for item in trace:
                self.assertIn(item["reason_code"], MATCH_RULE_REASON_CODES[item["rule_id"]])
                seen_rules.add(item["rule_id"])

        self.assertEqual(seen_rules, set(MATCH_RULE_REASON_CODES))


class StaffWorkflowAgentTests(unittest.TestCase):
    def test_workflow_requires_review_and_never_approves_or_releases(self):
        lost = TextReport("l1", "lost", "blue bottle", category_id=None)
        found = TextReport("f1", "found", "blue bottle", category_id="bottle")
        assessment = assess_candidate(lost, found, 0.7)

        recommendation = recommend_staff_workflow(assessment)
        output = recommendation.to_dict()

        self.assertEqual(recommendation.action, WorkflowAction.REQUEST_DETAILS)
        self.assertFalse(output["ownership_approved"])
        self.assertFalse(output["release_authorized"])
        self.assertIn("MISSING_DETAILS_REQUIRE_REVIEW", output["reason_codes"])
        self.assertIn("WF-R004", output["rule_ids"])
        self.assertIn("WF-R005", output["rule_ids"])

    def test_workflow_routes_conflicts_for_staff_inspection(self):
        lost = TextReport("l1", "lost", "blue bottle", category_id="bottle")
        found = TextReport("f1", "found", "blue bottle", category_id="wallet")
        recommendation = recommend_staff_workflow(assess_candidate(lost, found, 0.8))
        self.assertEqual(recommendation.action, WorkflowAction.REVIEW_CONFLICTS)
        self.assertFalse(recommendation.release_authorized)

    def test_workflow_routes_complete_agreement_for_staff_review(self):
        lost = TextReport("l1", "lost", "blue bottle", category_id="bottle", location_id="library", event_date="2026-11-16")
        found = TextReport("f1", "found", "blue bottle", category_id="bottle", location_id="library", event_date="2026-11-17")
        recommendation = recommend_staff_workflow(assess_candidate(lost, found, 0.8))
        self.assertEqual(recommendation.action, WorkflowAction.STAFF_REVIEW)
        self.assertFalse(recommendation.ownership_approved)
        self.assertFalse(recommendation.release_authorized)

    def test_ambiguous_category_requests_details_without_authorizing_release(self):
        lost = TextReport("l1", "lost", "blue item", category_id="Accessories")
        found = TextReport("f1", "found", "blue item", category_id="Accessories")
        recommendation = recommend_staff_workflow(assess_candidate(lost, found, 0.8))
        output = recommendation.to_dict()

        self.assertEqual(recommendation.action, WorkflowAction.REQUEST_DETAILS)
        self.assertIn("AMBIGUOUS_CATEGORY_REQUIRES_REVIEW", output["reason_codes"])
        self.assertFalse(output["ownership_approved"])
        self.assertFalse(output["release_authorized"])

    def test_every_workflow_rule_and_reason_is_traceable(self):
        assessments = [
            assess_candidate(*self._reports("bottle", "bottle"), 0.8),
            assess_candidate(*self._reports("bottle", "wallet"), 0.8),
            assess_candidate(*self._reports(None, "bottle"), 0.8),
            assess_candidate(*self._reports("Accessories", "bottle"), 0.8),
        ]
        seen_rules = set()

        for assessment in assessments:
            output = recommend_staff_workflow(assessment).to_dict()
            trace = output["rule_trace"]
            self.assertEqual(output["rule_ids"], [item["rule_id"] for item in trace])
            self.assertEqual(output["reason_codes"], [item["reason_code"] for item in trace])
            for item in trace:
                self.assertIn(item["reason_code"], WORKFLOW_RULE_REASON_CODES[item["rule_id"]])
                seen_rules.add(item["rule_id"])

        self.assertEqual(seen_rules, set(WORKFLOW_RULE_REASON_CODES))

    @staticmethod
    def _reports(lost_category, found_category):
        lost = TextReport(
            "l1",
            "lost",
            "blue item",
            category_id=lost_category,
            location_id="library",
            event_date="2026-11-16",
        )
        found = TextReport(
            "f1",
            "found",
            "blue item",
            category_id=found_category,
            location_id="library",
            event_date="2026-11-16",
        )
        return lost, found


if __name__ == "__main__":
    unittest.main()
