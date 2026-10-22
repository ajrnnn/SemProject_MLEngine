"""Deterministic, non-destructive processing of the Delhi Metro CSV."""

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "raw" / "delhi" / "delhimetrorail.csv"
OUTPUT = ROOT / "data" / "processed" / "delhi_metro.csv"
REPORT = ROOT / "data" / "processed" / "delhi_preprocessing_report.json"
COLUMNS = ["item_name", "description", "item_quantity", "station_name", "receiving_date", "receiving_time"]


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def prepare(source: Path = SOURCE, output: Path = OUTPUT, report_path: Path = REPORT) -> dict:
    if not source.is_file():
        raise FileNotFoundError(
            f"Delhi CSV missing at {source}. Download it from the source linked in "
            "docs/DATASET.md and place it at this local, Git-ignored path."
        )
    raw = source.read_bytes()
    with source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != COLUMNS:
            raise ValueError(f"Expected {COLUMNS}; found {reader.fieldnames}")
        rows = list(reader)
    missing = Counter()
    parsing_failures = Counter()
    modified = Counter()
    duplicates = 0
    seen = set()
    processed = []
    for index, row in enumerate(rows, 1):
        if None in row:
            raise ValueError(f"Unexpected extra field on data row {index}")
        key = tuple(row[name] for name in COLUMNS)
        if key in seen:
            duplicates += 1
        seen.add(key)
        clean = {"source_row": index}
        for name in COLUMNS:
            value = normalize(row[name] or "")
            if value != (row[name] or ""):
                modified[name] += 1
            if not value:
                missing[name] += 1
            clean[name] = value
        for name in ("item_name", "description", "station_name"):
            clean[name + "_normalized"] = clean[name].casefold()
        for name, fmt in (("receiving_date", "%d/%m/%Y"), ("receiving_time", "%H:%M:%S")):
            value = clean[name]
            try:
                parsed = datetime.strptime(value, fmt) if value else None
            except ValueError:
                parsed = None
                parsing_failures[name] += 1
            clean[name + "_iso"] = parsed.strftime("%Y-%m-%d" if name.endswith("date") else "%H:%M:%S") if parsed else ""
        processed.append(clean)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(processed[0]))
        writer.writeheader()
        writer.writerows(processed)
    report = {
        "source": str(source.relative_to(ROOT) if source.is_relative_to(ROOT) else source),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "original_rows": len(rows), "final_rows": len(processed),
        "duplicates_identified": duplicates, "duplicates_removed": 0,
        "missing_values": dict(missing), "parsing_failures": dict(parsing_failures),
        "whitespace_modified_rows_by_field": dict(modified),
        "normalization": "Whitespace collapsed; separate casefolded text columns; date DD/MM/YYYY and time HH:MM:SS parsed to ISO columns.",
        "excluded_records": [],
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(prepare(), indent=2))
