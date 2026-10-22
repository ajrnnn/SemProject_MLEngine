from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Report:
    report_id: str
    report_type: str
    description: str
    category: str = ""
    brand: str = ""
    model: str = ""
    colour: str = ""
    material: str = ""
    distinctive_features: tuple[str, ...] = field(default_factory=tuple)
    location: str = ""
    reported_at: datetime | None = None
    status: str = "active"
    image_reference: str = ""


@dataclass(frozen=True)
class LabelledPair:
    lost_report_id: str
    found_report_id: str
    label: str
    match_type: str
    notes: str


@dataclass(frozen=True)
class MatchCandidate:
    found_report_id: str
    score: float
    shared_characteristics: tuple[str, ...]
    conflicting_details: tuple[str, ...]
    missing_information: tuple[str, ...]
    explanation: str
    requires_human_verification: bool = True

