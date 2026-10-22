"""Generate the labelled, inspectable CAT 2 modelling table from raw sources."""

import csv
from collections import Counter
from pathlib import Path

from matching_system.data_loader import load_labelled_pairs, load_reports
from matching_system.feature_builder import FEATURE_NAMES, pair_features
from scripts.prepare_campus_data import ROOT, prepare

LABEL_TO_TARGET = {"match": 1, "plausible": 0, "non_match": 0}
OUTPUT = ROOT / "data" / "processed" / "modelling_pairs.csv"


def build(output: Path = OUTPUT) -> dict:
    correction = prepare()
    reports = {report.report_id: report for report in load_reports(ROOT / "data/processed/synthetic_campus_reports.csv")}
    pairs = load_labelled_pairs(ROOT / "data/raw/campus/labelled_campus_pairs.csv")
    rows = []
    seen = set()
    for pair in pairs:
        key = (pair.lost_report_id, pair.found_report_id)
        if key in seen:
            raise ValueError(f"Duplicate labelled pair: {key}")
        seen.add(key)
        if pair.label not in LABEL_TO_TARGET:
            raise ValueError(f"Unknown pair label: {pair.label}")
        try:
            lost, found = reports[pair.lost_report_id], reports[pair.found_report_id]
        except KeyError as exc:
            raise ValueError(f"Label refers to missing report: {exc}") from exc
        rows.append({"lost_report_id": lost.report_id, "found_report_id": found.report_id,
                     "original_label": pair.label, **pair_features(lost, found),
                     "target": LABEL_TO_TARGET[pair.label]})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["lost_report_id", "found_report_id", "original_label", *FEATURE_NAMES, "target"])
        writer.writeheader()
        writer.writerows(rows)
    return {"rows": len(rows), "labels": dict(Counter(row["original_label"] for row in rows)),
            "targets": dict(Counter(row["target"] for row in rows)), "raw_corrections": correction,
            "output": str(output)}


if __name__ == "__main__":
    print(build())
