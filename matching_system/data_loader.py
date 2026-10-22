from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from .models import LabelledPair, Report
from .normalization import split_features


REPORT_COLUMNS = {
    "report_id",
    "report_type",
    "description",
    "category",
    "brand",
    "model",
    "colour",
    "material",
    "distinctive_features",
    "location",
    "reported_at",
    "status",
    "image_reference",
}

LABEL_COLUMNS = {"lost_report_id", "found_report_id", "label", "match_type", "notes"}


def parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def validate_columns(path: Path, required_columns: set[str]) -> None:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
    missing = sorted(required_columns - columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {', '.join(missing)}")


def load_reports(path: str | Path) -> list[Report]:
    csv_path = Path(path)
    validate_columns(csv_path, REPORT_COLUMNS)
    reports: list[Report] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            reports.append(
                Report(
                    report_id=row["report_id"],
                    report_type=row["report_type"],
                    description=row["description"],
                    category=row["category"],
                    brand=row["brand"],
                    model=row["model"],
                    colour=row["colour"],
                    material=row["material"],
                    distinctive_features=split_features(row["distinctive_features"]),
                    location=row["location"],
                    reported_at=parse_datetime(row["reported_at"]),
                    status=row["status"],
                    image_reference=row["image_reference"],
                )
            )
    return reports


def load_labelled_pairs(path: str | Path) -> list[LabelledPair]:
    csv_path = Path(path)
    validate_columns(csv_path, LABEL_COLUMNS)
    pairs: list[LabelledPair] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            pairs.append(
                LabelledPair(
                    lost_report_id=row["lost_report_id"],
                    found_report_id=row["found_report_id"],
                    label=row["label"],
                    match_type=row["match_type"],
                    notes=row["notes"],
                )
            )
    return pairs

