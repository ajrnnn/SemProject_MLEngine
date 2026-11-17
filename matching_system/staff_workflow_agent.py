"""Staff-workflow recommendation; ownership and release remain human decisions.

Example serialized output::

    {
      "lost_report_id": "l1",
      "found_report_id": "f1",
      "action": "staff_review",
      "ownership_approved": false,
      "release_authorized": false,
      "rule_ids": ["WF-R001"],
      "reason_codes": ["STAFF_REVIEW_REQUIRED",
                       "OWNERSHIP_NOT_AUTOMATED",
                       "RELEASE_NOT_AUTOMATED"]
    }
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from matching_system.matching_agent import MatchAssessment


class WorkflowAction(str, Enum):
    STAFF_REVIEW = "staff_review"


RULE_STAFF_REVIEW_REQUIRED = "WF-R001"
REASON_STAFF_REVIEW_REQUIRED = "STAFF_REVIEW_REQUIRED"
REASON_OWNERSHIP_NOT_AUTOMATED = "OWNERSHIP_NOT_AUTOMATED"
REASON_RELEASE_NOT_AUTOMATED = "RELEASE_NOT_AUTOMATED"


@dataclass(frozen=True)
class WorkflowRecommendation:
    lost_report_id: str
    found_report_id: str
    action: WorkflowAction
    ownership_approved: bool
    release_authorized: bool
    rule_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, str | bool | list[str]]:
        return {
            "lost_report_id": self.lost_report_id,
            "found_report_id": self.found_report_id,
            "action": self.action.value,
            "ownership_approved": self.ownership_approved,
            "release_authorized": self.release_authorized,
            "rule_ids": list(self.rule_ids),
            "reason_codes": list(self.reason_codes),
        }


def recommend_staff_workflow(assessment: MatchAssessment) -> WorkflowRecommendation:
    """Route every assessment to staff; never approve ownership or release."""
    return WorkflowRecommendation(
        lost_report_id=assessment.lost_report_id,
        found_report_id=assessment.found_report_id,
        action=WorkflowAction.STAFF_REVIEW,
        ownership_approved=False,
        release_authorized=False,
        rule_ids=(RULE_STAFF_REVIEW_REQUIRED,),
        reason_codes=(
            REASON_STAFF_REVIEW_REQUIRED,
            REASON_OWNERSHIP_NOT_AUTOMATED,
            REASON_RELEASE_NOT_AUTOMATED,
        ),
    )
