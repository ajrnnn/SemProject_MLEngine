"""Staff-workflow recommendation; ownership and release remain human decisions.

Example serialized output::

    {
      "lost_report_id": "l1",
      "found_report_id": "f1",
      "action": "staff_review",
      "ownership_approved": false,
      "release_authorized": false,
      "rule_ids": ["WF-R001", "WF-R004", "WF-R005"],
      "reason_codes": ["STAFF_REVIEW_REQUIRED",
                       "OWNERSHIP_NOT_AUTOMATED",
                       "RELEASE_NOT_AUTOMATED"],
      "rule_trace": [
        {"rule_id": "WF-R003", "reason_code": "STAFF_REVIEW_REQUIRED",
         "fact_id": null},
        {"rule_id": "WF-R004", "reason_code": "OWNERSHIP_NOT_AUTOMATED",
         "fact_id": "ownership"},
        {"rule_id": "WF-R005", "reason_code": "RELEASE_NOT_AUTOMATED",
         "fact_id": "release"}
      ]
    }
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from matching_system.matching_agent import FactStatus, MatchAssessment


class WorkflowAction(str, Enum):
    STAFF_REVIEW = "staff_review"
    REVIEW_CONFLICTS = "review_conflicts"
    REQUEST_DETAILS = "request_details"


RULE_STAFF_REVIEW_REQUIRED = "WF-R001"
RULE_REVIEW_CONFLICTS = "WF-R002"
RULE_REQUEST_DETAILS = "WF-R003"
RULE_OWNERSHIP_NOT_AUTOMATED = "WF-R004"
RULE_RELEASE_NOT_AUTOMATED = "WF-R005"
REASON_STAFF_REVIEW_REQUIRED = "STAFF_REVIEW_REQUIRED"
REASON_CONFLICTS_REQUIRE_REVIEW = "CONFLICTS_REQUIRE_REVIEW"
REASON_MISSING_DETAILS = "MISSING_DETAILS_REQUIRE_REVIEW"
REASON_AMBIGUOUS_CATEGORY = "AMBIGUOUS_CATEGORY_REQUIRES_REVIEW"
REASON_OWNERSHIP_NOT_AUTOMATED = "OWNERSHIP_NOT_AUTOMATED"
REASON_RELEASE_NOT_AUTOMATED = "RELEASE_NOT_AUTOMATED"

RULE_REASON_CODES = {
    RULE_STAFF_REVIEW_REQUIRED: (REASON_STAFF_REVIEW_REQUIRED,),
    RULE_REVIEW_CONFLICTS: (REASON_CONFLICTS_REQUIRE_REVIEW,),
    RULE_REQUEST_DETAILS: (REASON_MISSING_DETAILS, REASON_AMBIGUOUS_CATEGORY),
    RULE_OWNERSHIP_NOT_AUTOMATED: (REASON_OWNERSHIP_NOT_AUTOMATED,),
    RULE_RELEASE_NOT_AUTOMATED: (REASON_RELEASE_NOT_AUTOMATED,),
}


@dataclass(frozen=True)
class WorkflowRuleTrace:
    rule_id: str
    reason_code: str
    fact_id: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "rule_id": self.rule_id,
            "reason_code": self.reason_code,
            "fact_id": self.fact_id,
        }


@dataclass(frozen=True)
class WorkflowRecommendation:
    lost_report_id: str
    found_report_id: str
    action: WorkflowAction
    ownership_approved: bool
    release_authorized: bool
    rule_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    rule_trace: tuple[WorkflowRuleTrace, ...] = ()

    def to_dict(self) -> dict[
        str, str | bool | list[str] | list[dict[str, str | None]]
    ]:
        return {
            "lost_report_id": self.lost_report_id,
            "found_report_id": self.found_report_id,
            "action": self.action.value,
            "ownership_approved": self.ownership_approved,
            "release_authorized": self.release_authorized,
            "rule_ids": list(self.rule_ids),
            "reason_codes": list(self.reason_codes),
            "rule_trace": [trace.to_dict() for trace in self.rule_trace],
        }


def recommend_staff_workflow(assessment: MatchAssessment) -> WorkflowRecommendation:
    """Choose the next staff task; never approve ownership or release."""
    if assessment.evidence_state is FactStatus.CONFLICT:
        action, rule, reason = (
            WorkflowAction.REVIEW_CONFLICTS,
            RULE_REVIEW_CONFLICTS,
            REASON_CONFLICTS_REQUIRE_REVIEW,
        )
        action_fact_id = next(
            (fact.fact_id for fact in assessment.facts if fact.status is FactStatus.CONFLICT),
            None,
        )
    elif any(fact.status is FactStatus.AMBIGUOUS for fact in assessment.facts):
        action, rule, reason = (
            WorkflowAction.REQUEST_DETAILS,
            RULE_REQUEST_DETAILS,
            REASON_AMBIGUOUS_CATEGORY,
        )
        action_fact_id = next(
            (fact.fact_id for fact in assessment.facts if fact.status is FactStatus.AMBIGUOUS),
            None,
        )
    elif any(fact.status is FactStatus.UNKNOWN for fact in assessment.facts):
        action, rule, reason = (
            WorkflowAction.REQUEST_DETAILS,
            RULE_REQUEST_DETAILS,
            REASON_MISSING_DETAILS,
        )
        action_fact_id = next(
            (fact.fact_id for fact in assessment.facts if fact.status is FactStatus.UNKNOWN),
            None,
        )
    else:
        action, rule, reason = (
            WorkflowAction.STAFF_REVIEW,
            RULE_STAFF_REVIEW_REQUIRED,
            REASON_STAFF_REVIEW_REQUIRED,
        )
        action_fact_id = None
    rule_trace = (
        WorkflowRuleTrace(rule, reason, action_fact_id),
        WorkflowRuleTrace(
            RULE_OWNERSHIP_NOT_AUTOMATED,
            REASON_OWNERSHIP_NOT_AUTOMATED,
            "ownership",
        ),
        WorkflowRuleTrace(
            RULE_RELEASE_NOT_AUTOMATED,
            REASON_RELEASE_NOT_AUTOMATED,
            "release",
        ),
    )
    return WorkflowRecommendation(
        lost_report_id=assessment.lost_report_id,
        found_report_id=assessment.found_report_id,
        action=action,
        ownership_approved=False,
        release_authorized=False,
        rule_ids=tuple(trace.rule_id for trace in rule_trace),
        reason_codes=tuple(trace.reason_code for trace in rule_trace),
        rule_trace=rule_trace,
    )
