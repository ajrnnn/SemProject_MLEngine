"""Local, synthetic-only API preview. It does not store reports or verify claims."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from matching_system.nlp_retrieval import TextReport, load_text_reports_csv
from matching_system.pipeline import MatchingPipeline


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "data/fixtures/day3/demo_reports.csv"
_reports = load_text_reports_csv(FIXTURE_PATH)
pipeline = MatchingPipeline([report for report in _reports if report.report_type == "found"])

app = FastAPI(title="Lost & Found staff matching preview")

_EMAIL_PATTERN = re.compile(r"\b[\w.!#$%&'*+/=?^`{|}~-]+@[\w-]+(?:\.[\w-]+)+\b")
_PHONE_PATTERN = re.compile(r"(?<!\w)\+?(?:\d[\s().-]*){7,15}(?!\w)")
_PRIVATE_ID_PATTERN = re.compile(
    r"\b(?:student[_\s-]*id|national[_\s-]*id|id[_\s-]*number|passport(?:[_\s-]*(?:number|no))?)"
    r"\s*(?::|#|=|-)?\s*(?=[a-z0-9-]{4,}\b)(?=[a-z0-9-]*\d)[a-z0-9-]{4,}\b",
    re.IGNORECASE,
)


def _contains_obvious_private_data(value: str) -> bool:
    without_dates = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", value)
    return any(
        pattern.search(without_dates)
        for pattern in (_EMAIL_PATTERN, _PHONE_PATTERN, _PRIVATE_ID_PATTERN)
    )


class PreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    item_name: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=4000)
    category_id: str | None = None
    location_id: str | None = None
    event_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    limit: int = Field(default=5, ge=1, le=5)

    @field_validator("event_date")
    @classmethod
    def valid_calendar_date(cls, value: str | None) -> str | None:
        if value is not None:
            date.fromisoformat(value)
        return value

    @field_validator("item_name", "description", "category_id", "location_id")
    @classmethod
    def reject_obvious_private_data(cls, value: str | None) -> str | None:
        if value is not None and _contains_obvious_private_data(value):
            raise ValueError("Text contains a disallowed private-data pattern")
        return value


@app.exception_handler(RequestValidationError)
async def redact_validation_error(_request, _error):
    # FastAPI's default error can echo rejected private fields and their values.
    return JSONResponse(status_code=422, content={"detail": "Invalid general-item preview request"})


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {"status": "ok", "mode": "synthetic_preview", "persistence": False}


@app.post("/preview/matches")
def preview_matches(request: PreviewRequest) -> dict[str, object]:
    lost = TextReport(
        report_id="preview-query",
        report_type="lost",
        item_name=request.item_name,
        description=request.description,
        category_id=request.category_id,
        location_id=request.location_id,
        event_date=request.event_date,
    )
    return {"mode": "synthetic_preview", **pipeline.recommend(lost, limit=request.limit)}
