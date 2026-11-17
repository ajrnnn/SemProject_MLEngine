"""Conservative rule-based evidence assessment for retrieved report pairs.

Call ``assess_candidate(lost, found, text_similarity)`` with the retrieval
score in the inclusive range [0, 1]. Category disagreement excludes a
candidate; location and event-date differences remain non-dispositive.
Similarity is returned as lexical evidence, not interpreted as a probability.

Example serialized output::

    {
      "lost_report_id": "l1",
      "found_report_id": "f1",
      "text_similarity": 0.72,
      "evidence_state": "conflict",
      "candidate_recommendation": "staff_review",
      "facts": [
        {"fact_id": "category_id", "status": "agreement",
         "lost_value": "electronics", "found_value": "electronics",
         "reason_code": "CATEGORY_AGREEMENT"},
        {"fact_id": "location_id", "status": "conflict",
         "lost_value": "library", "found_value": "cafeteria",
         "reason_code": "LOCATION_DIFFERENCE_NON_DISPOSITIVE"},
        {"fact_id": "event_date", "status": "unknown",
         "lost_value": null, "found_value": "2026-11-16",
         "reason_code": "EVENT_DATE_UNKNOWN"}
      ],
      "rule_ids": ["MA-R001", "MA-R005", "MA-R009", "MA-R010"],
      "reason_codes": ["CATEGORY_AGREEMENT",
                       "LOCATION_DIFFERENCE_NON_DISPOSITIVE",
                       "EVENT_DATE_UNKNOWN", "TEXT_SIMILARITY_RECORDED"]
    }
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from matching_system.nlp_retrieval import TextReport


class FactStatus(str, Enum):
    AGREEMENT = "agreement"
    CONFLICT = "conflict"
    UNKNOWN = "unknown"


class CandidateRecommendation(str, Enum):
    EXCLUDE_CANDIDATE = "exclude_candidate"
    STAFF_REVIEW = "staff_review"


FACT_CATEGORY_ID = "category_id"
FACT_LOCATION_ID = "location_id"
FACT_EVENT_DATE = "event_date"
FACT_TEXT_SIMILARITY = "text_similarity"

RULE_CATEGORY_AGREEMENT = "MA-R001"
RULE_CATEGORY_CONFLICT = "MA-R002"
RULE_CATEGORY_UNKNOWN = "MA-R003"
RULE_LOCATION_AGREEMENT = "MA-R004"
RULE_LOCATION_DIFFERENCE = "MA-R005"
RULE_LOCATION_UNKNOWN = "MA-R006"
RULE_EVENT_DATE_AGREEMENT = "MA-R007"
RULE_EVENT_DATE_DIFFERENCE = "MA-R008"
RULE_EVENT_DATE_UNKNOWN = "MA-R009"
RULE_TEXT_SIMILARITY_RECORDED = "MA-R010"

REASON_CATEGORY_AGREEMENT = "CATEGORY_AGREEMENT"
REASON_CATEGORY_CONFLICT = "CATEGORY_CONFLICT"
REASON_CATEGORY_UNKNOWN = "CATEGORY_UNKNOWN"
REASON_LOCATION_AGREEMENT = "LOCATION_AGREEMENT"
REASON_LOCATION_DIFFERENCE = "LOCATION_DIFFERENCE_NON_DISPOSITIVE"
REASON_LOCATION_UNKNOWN = "LOCATION_UNKNOWN"
REASON_EVENT_DATE_AGREEMENT = "EVENT_DATE_AGREEMENT"
REASON_EVENT_DATE_DIFFERENCE = "EVENT_DATE_DIFFERENCE_NON_DISPOSITIVE"
REASON_EVENT_DATE_UNKNOWN = "EVENT_DATE_UNKNOWN"
REASON_TEXT_SIMILARITY_RECORDED = "TEXT_SIMILARITY_RECORDED"


@dataclass(frozen=True)
class FactEvidence:
    fact_id: str
    status: FactStatus
    lost_value: str | None
    found_value: str | None
    reason_code: str

    def to_dict(self) -> dict[str, str | None]:
        return {
            "fact_id": self.fact_id,
            "status": self.status.value,
            "lost_value": self.lost_value,
            "found_value": self.found_value,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class MatchAssessment:
    lost_report_id: str
    found_report_id: str
    text_similarity: float
    evidence_state: FactStatus
    candidate_recommendation: CandidateRecommendation
    facts: tuple[FactEvidence, ...]
    rule_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, str | float | list[dict[str, str | None]] | list[str]]:
        return {
            "lost_report_id": self.lost_report_id,
            "found_report_id": self.found_report_id,
            "text_similarity": self.text_similarity,
            "evidence_state": self.evidence_state.value,
            "candidate_recommendation": self.candidate_recommendation.value,
            "facts": [fact.to_dict() for fact in self.facts],
            "rule_ids": list(self.rule_ids),
            "reason_codes": list(self.reason_codes),
        }


def assess_candidate(
    lost: TextReport,
    found: TextReport,
    text_similarity: float,
) -> MatchAssessment:
    """Assess structured evidence without converting similarity into a verdict."""
    if lost.report_type != "lost":
        raise ValueError("The first report must have report_type='lost'")
    if found.report_type != "found":
        raise ValueError("The second report must have report_type='found'")
    if not math.isfinite(text_similarity) or not 0 <= text_similarity <= 1:
        raise ValueError("text_similarity must be a finite value between 0 and 1")

    facts: list[FactEvidence] = []
    rule_ids: list[str] = []
    reason_codes: list[str] = []

    category, rule_id, reason = _compare(
        FACT_CATEGORY_ID,
        lost.category_id,
        found.category_id,
        RULE_CATEGORY_AGREEMENT,
        RULE_CATEGORY_CONFLICT,
        RULE_CATEGORY_UNKNOWN,
        REASON_CATEGORY_AGREEMENT,
        REASON_CATEGORY_CONFLICT,
        REASON_CATEGORY_UNKNOWN,
    )
    facts.append(category)
    rule_ids.append(rule_id)
    reason_codes.append(reason)

    location, rule_id, reason = _compare(
        FACT_LOCATION_ID,
        lost.location_id,
        found.location_id,
        RULE_LOCATION_AGREEMENT,
        RULE_LOCATION_DIFFERENCE,
        RULE_LOCATION_UNKNOWN,
        REASON_LOCATION_AGREEMENT,
        REASON_LOCATION_DIFFERENCE,
        REASON_LOCATION_UNKNOWN,
    )
    facts.append(location)
    rule_ids.append(rule_id)
    reason_codes.append(reason)

    event_date, rule_id, reason = _compare(
        FACT_EVENT_DATE,
        lost.event_date,
        found.event_date,
        RULE_EVENT_DATE_AGREEMENT,
        RULE_EVENT_DATE_DIFFERENCE,
        RULE_EVENT_DATE_UNKNOWN,
        REASON_EVENT_DATE_AGREEMENT,
        REASON_EVENT_DATE_DIFFERENCE,
        REASON_EVENT_DATE_UNKNOWN,
    )
    facts.append(event_date)
    rule_ids.append(rule_id)
    reason_codes.append(reason)

    rule_ids.append(RULE_TEXT_SIMILARITY_RECORDED)
    reason_codes.append(REASON_TEXT_SIMILARITY_RECORDED)

    if any(fact.status is FactStatus.CONFLICT for fact in facts):
        evidence_state = FactStatus.CONFLICT
    elif any(fact.status is FactStatus.AGREEMENT for fact in facts):
        evidence_state = FactStatus.AGREEMENT
    else:
        evidence_state = FactStatus.UNKNOWN

    recommendation = (
        CandidateRecommendation.EXCLUDE_CANDIDATE
        if category.status is FactStatus.CONFLICT
        else CandidateRecommendation.STAFF_REVIEW
    )
    return MatchAssessment(
        lost_report_id=lost.report_id,
        found_report_id=found.report_id,
        text_similarity=float(text_similarity),
        evidence_state=evidence_state,
        candidate_recommendation=recommendation,
        facts=tuple(facts),
        rule_ids=tuple(rule_ids),
        reason_codes=tuple(reason_codes),
    )


def _compare(
    fact_id: str,
    lost_value: str | None,
    found_value: str | None,
    agreement_rule: str,
    conflict_rule: str,
    unknown_rule: str,
    agreement_reason: str,
    conflict_reason: str,
    unknown_reason: str,
) -> tuple[FactEvidence, str, str]:
    known_lost = lost_value.strip() if lost_value and lost_value.strip() else None
    known_found = found_value.strip() if found_value and found_value.strip() else None
    if known_lost is None or known_found is None:
        status, rule_id, reason = FactStatus.UNKNOWN, unknown_rule, unknown_reason
    elif known_lost == known_found:
        status, rule_id, reason = FactStatus.AGREEMENT, agreement_rule, agreement_reason
    else:
        status, rule_id, reason = FactStatus.CONFLICT, conflict_rule, conflict_reason
    return (
        FactEvidence(fact_id, status, known_lost, known_found, reason),
        rule_id,
        reason,
    )
