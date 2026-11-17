"""Local, synthetic-only API preview. It does not store reports or verify claims."""

from __future__ import annotations

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
