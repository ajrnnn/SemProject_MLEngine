"""Text-only candidate retrieval; dataset and knowledge rules stay separate."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class TextReport:
    report_id: str
    report_type: str
    description: str
    item_name: str = ""
    category_id: str | None = None
    location_id: str | None = None
    event_date: str | None = None


def normalize_report_text(value: str | None) -> str:
    """Normalize spelling surface only; do not infer item identity or attributes."""
    text = (value or "").casefold().replace("-", " ")
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text)).strip()


def load_text_reports_csv(path: str | Path, columns: dict[str, str] | None = None) -> list[TextReport]:
    """Import a CSV through an explicit field map; private columns are never copied."""
    names = {field: field for field in TextReport.__dataclass_fields__}
    names.update(columns or {})
    if any(source.lower() in {"id_number", "student_id", "national_id"} for source in names.values()):
        raise ValueError("Private ID fields cannot enter general-item retrieval")
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {names[field] for field in ("report_id", "report_type", "description")}
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"Missing report columns: {', '.join(sorted(missing))}")
        reports = []
        for row in reader:
            values = {field: (row.get(source) or "").strip() for field, source in names.items()}
            if not values["report_id"] or values["report_type"] not in {"lost", "found"}:
                raise ValueError("Every report needs an ID and lost/found type")
            reports.append(TextReport(**values))
    if len({report.report_id for report in reports}) != len(reports):
        raise ValueError("Report IDs must be unique")
    return reports


class TfidfRanker:
    """Fit on found reports only and return lexical evidence for later agents."""

    def __init__(self, found_reports: list[TextReport]):
        self.reports: list[TextReport] = []
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), strip_accents="unicode")
        self.matrix = None
        self.replace_inventory(found_reports)

    def replace_inventory(self, found_reports: list[TextReport]) -> None:
        """Refit the index after the found-report inventory changes."""
        if any(report.report_type != "found" for report in found_reports):
            raise ValueError("The inventory must contain found reports only")
        if len({report.report_id for report in found_reports}) != len(found_reports):
            raise ValueError("Found report IDs must be unique")
        next_reports = list(found_reports)
        next_vectorizer = TfidfVectorizer(ngram_range=(1, 2), strip_accents="unicode")
        next_matrix = None
        corpus = [self._text(report) for report in next_reports]
        if any(corpus):
            try:
                next_matrix = next_vectorizer.fit_transform(corpus)
            except ValueError as error:
                if "empty vocabulary" not in str(error):
                    raise
        self.reports = next_reports
        self.vectorizer = next_vectorizer
        self.matrix = next_matrix

    @staticmethod
    def _text(report: TextReport) -> str:
        return normalize_report_text(f"{report.item_name} {report.description}")

    def rank(
        self, lost: TextReport, limit: int = 5, min_similarity: float = 0.0
    ) -> list[dict[str, str | float]]:
        if lost.report_type != "lost":
            raise ValueError("Ranking requires a lost report")
        if not 1 <= limit <= 5:
            raise ValueError("limit must be between one and five")
        if not 0.0 <= min_similarity <= 1.0:
            raise ValueError("min_similarity must be between zero and one")
        if self.matrix is None or not self._text(lost):
            return []
        vector = self.vectorizer.transform([self._text(lost)])
        similarities = cosine_similarity(vector, self.matrix)[0]
        return [
            {"found_report_id": report.report_id, "text_similarity": round(float(score), 6)}
            for report, score in sorted(zip(self.reports, similarities), key=lambda item: (-item[1], item[0].report_id))
            if score > 0 and score >= min_similarity
        ][:limit]
