"""Compose retrieval and knowledge-agent decisions for a staff preview."""

from __future__ import annotations

from matching_system.matching_agent import FactStatus, MatchAssessment, assess_candidate
from matching_system.nlp_retrieval import TextReport, TfidfRanker
from matching_system.staff_workflow_agent import (
    WorkflowAction,
    WorkflowRecommendation,
    recommend_staff_workflow,
)


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
            matches.append({
                **assessment.to_dict(),
                "explanation": explain_candidate(assessment, workflow),
                "workflow": workflow.to_dict(),
            })
        return {
            "status": "possible_matches" if matches else "no_lexical_candidates",
            "score_meaning": "TF-IDF cosine similarity, not match or ownership probability",
            "matches": matches,
        }


_FACT_LABELS = {
    "category_id": "category",
    "location_id": "location",
    "event_date": "event date",
}


def explain_candidate(
    assessment: MatchAssessment,
    workflow: WorkflowRecommendation,
) -> str:
    """Build a plain-language explanation without exposing report field values."""
    fact_summaries = []
    for fact in assessment.facts:
        label = _FACT_LABELS.get(fact.fact_id)
        if label is None:
            continue
        if fact.status is FactStatus.AGREEMENT:
            detail = "agrees"
        elif fact.status is FactStatus.CONFLICT:
            detail = "differs"
        elif fact.status is FactStatus.AMBIGUOUS:
            detail = "is broad or ambiguous"
        else:
            detail = "is missing or unknown"
        fact_summaries.append(f"{label} {detail}")

    facts_text = "; ".join(fact_summaries) if fact_summaries else "no structured facts are available"
    if workflow.action is WorkflowAction.REVIEW_CONFLICTS:
        next_action = "Staff should review the conflicting details."
    elif workflow.action is WorkflowAction.REQUEST_DETAILS:
        next_action = "Staff should request or verify additional details."
    else:
        next_action = "Staff should review this possible match."
    return (
        f"Facts: {facts_text}. {next_action} "
        "Text similarity is lexical evidence, not a probability. "
        "Ownership is unverified; release is not authorized."
    )
