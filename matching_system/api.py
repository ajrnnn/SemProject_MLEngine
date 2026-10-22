from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .data_loader import load_reports
from .matcher import rank_candidates
from .models import Report

DATA_PATH = Path(__file__).resolve().parent.parent / "data/processed/synthetic_campus_reports.csv"

app = FastAPI(title="Campus Lost and Found Matching API")


class MatchRequest(BaseModel):
    lost_report_id: str = Field(..., examples=["lost-001"])
    limit: int = Field(default=5, ge=1, le=10)
    min_score: float = Field(default=30.0, ge=0, le=100)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/reports")
def list_reports() -> list[dict[str, object]]:
    # Prototype inventory excludes descriptions and proof-like details.
    return [{"report_id": r.report_id, "report_type": r.report_type, "category": r.category, "status": r.status}
            for r in load_reports(DATA_PATH)]


@app.post("/matches")
def find_matches(request: MatchRequest) -> dict[str, object]:
    reports = load_reports(DATA_PATH)
    lost_reports = {report.report_id: report for report in reports if report.report_type == "lost"}
    found_reports = [report for report in reports if report.report_type == "found"]
    lost = lost_reports.get(request.lost_report_id)
    if not lost:
        raise HTTPException(status_code=404, detail="Lost report not found")
    matches = rank_candidates(lost, found_reports, limit=request.limit, min_score=request.min_score)
    return {
        "lost_report_id": lost.report_id,
        "status": "potential_matches" if matches else "no_strong_match",
        "matches": [candidate.__dict__ for candidate in matches],
    }


@app.post("/reports")
def create_report_placeholder(report: dict[str, object]) -> dict[str, object]:
    return {
        "status": "not_persisted",
        "message": "Database persistence is intentionally deferred until the matching prototype is evaluated.",
        "received_fields": sorted(report),
    }

