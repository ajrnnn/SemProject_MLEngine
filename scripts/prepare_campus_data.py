"""Repair six shifted synthetic CSV rows without changing the source file."""

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "raw" / "campus" / "synthetic_campus_reports.csv"
OUTPUT = ROOT / "data" / "processed" / "synthetic_campus_reports.csv"


def prepare(source: Path = SOURCE, output: Path = OUTPUT) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    repaired = []
    with source.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = reader.fieldnames
    if not columns:
        raise ValueError("Synthetic report CSV has no header")
    for row in rows:
        if row.get(None) == [""] and not row["colour"] and row["material"]:
            # Six source rows have an extra empty field after category.
            for previous, following in zip(columns[6:], columns[7:]):
                row[previous] = row[following]
            row[columns[-1]] = row[None][0]
            row.pop(None)
            repaired.append(row["report_id"])
        if row.get(None) is not None:
            raise ValueError(f"Unexpected extra columns in {row['report_id']}")
        if not row["reported_at"].startswith("20"):
            raise ValueError(f"Invalid timestamp in {row['report_id']}")
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return {"source_rows": len(rows), "output_rows": len(rows), "repaired_ids": repaired}


if __name__ == "__main__":
    print(prepare())
