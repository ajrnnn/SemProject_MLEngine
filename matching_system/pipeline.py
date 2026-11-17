"""Compose retrieval and knowledge-agent decisions for a staff preview."""

from __future__ import annotations

from matching_system.matching_agent import assess_candidate
from matching_system.nlp_retrieval import TextReport, TfidfRanker
from matching_system.staff_workflow_agent import recommend_staff_workflow


class MatchingPipeline:
    def __init__(self, found_reports: list[TextReport]):
        self.replace_inventory(found_reports)

    def replace_inventory(self, found_reports: list[TextReport]) -> None:
        """Refresh both the lexical index and its report lookup together."""
        reports = list(found_reports)
        ranker = TfidfRanker(reports)
        self._ranker = ranker
        self._found_by_id = {report.report_id: report for report in reports}

    def recommend(self, lost: TextReport, limit: int = 5) -> dict[str, object]:
        if lost.report_type != "lost":
            raise ValueError("A lost report is required")
        matches = []
        for candidate in self._ranker.rank(lost, limit=limit):
            found = self._found_by_id[candidate["found_report_id"]]
            assessment = assess_candidate(lost, found, candidate["text_similarity"])
            workflow = recommend_staff_workflow(assessment)
            matches.append({**assessment.to_dict(), "workflow": workflow.to_dict()})
        return {
            "status": "possible_matches" if matches else "no_lexical_candidates",
            "score_meaning": "TF-IDF cosine similarity, not match or ownership probability",
            "matches": matches,
        }
