"""Run a five-minute synthetic report-to-review walkthrough."""

from __future__ import annotations

import json
from pathlib import Path

from matching_system.nlp_retrieval import TextReport, load_text_reports_csv
from matching_system.pipeline import MatchingPipeline


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data/fixtures/day3/demo_reports.csv"


def main() -> None:
    reports = load_text_reports_csv(FIXTURES)
    pipeline = MatchingPipeline([report for report in reports if report.report_type == "found"])
    lost = next(report for report in reports if report.report_id == "demo-lost-bottle")
    no_match = TextReport("demo-lost-telescope", "lost", "Violet telescope marked SYNTHETIC-X999")
    print(json.dumps({
        "fixture_kind": "synthetic engineering demo; not campus accuracy",
        "bottle_query": pipeline.recommend(lost, limit=3),
        "no_match_query": pipeline.recommend(no_match),
    }, indent=2))


if __name__ == "__main__":
    main()
