"""Validate and rebuild an in-memory found-report index from a reviewed CSV."""

from __future__ import annotations

import argparse
from pathlib import Path

from matching_system.nlp_retrieval import TfidfRanker, load_text_reports_csv


DEFAULT_FIXTURE = Path(__file__).resolve().parents[1] / "data/fixtures/day3/demo_reports.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="?", type=Path, default=DEFAULT_FIXTURE)
    args = parser.parse_args()
    reports = load_text_reports_csv(args.csv)
    found = [report for report in reports if report.report_type == "found"]
    ranker = TfidfRanker(found)
    print(f"Found reports indexed: {len(ranker.reports)}")
    print(f"Vocabulary terms: {len(ranker.vectorizer.vocabulary_ if ranker.matrix is not None else {})}")
    print("Index is in memory only; restart or call replace_inventory after source changes.")


if __name__ == "__main__":
    main()
