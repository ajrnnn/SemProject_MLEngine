"""Check structural invariants in the generated Delhi pair dataset."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from scripts.create_delhi_experiment import PAIRS, SPLIT


def _read_pairs(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"lost_report_id", "found_report_id", "match", "label_basis"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} is missing columns: {', '.join(sorted(missing))}")
        return list(reader)


def _read_split(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        split = json.load(handle)
    if not isinstance(split, dict) or not isinstance(split.get("splits"), dict):
        raise ValueError(f"{path} must contain a 'splits' object")
    for name in ("development", "test"):
        if not isinstance(split["splits"].get(name), dict):
            raise ValueError(f"{path} must contain a '{name}' split")
    return split


def validate(pairs_path: Path = PAIRS, split_path: Path = SPLIT) -> dict[str, int]:
    """Raise ValueError with all found issues; otherwise return checked counts."""
    pairs = _read_pairs(pairs_path)
    split = _read_split(split_path)
    errors = []
    pairs_by_lost = defaultdict(list)
    if not pairs:
        errors.append("pair table contains no candidate pairs")

    for line, pair in enumerate(pairs, start=2):
        lost_id = (pair.get("lost_report_id") or "").strip()
        found_id = (pair.get("found_report_id") or "").strip()
        if not lost_id or not found_id:
            errors.append(f"pairs CSV row {line}: lost and found IDs must not be empty")
            continue
        pairs_by_lost[lost_id].append(pair)

    found_ids = [(pair.get("found_report_id") or "").strip() for pair in pairs
                 if (pair.get("found_report_id") or "").strip()]
    if len(found_ids) != len(set(found_ids)):
        errors.append("a found ID is reused in more than one candidate pair")

    for lost_id, candidates in sorted(pairs_by_lost.items()):
        if len(candidates) != 3:
            errors.append(f"{lost_id}: expected exactly 3 candidate pairs, found {len(candidates)}")

        labels = []
        for pair in candidates:
            label = (pair.get("match") or "").strip()
            basis = (pair.get("label_basis") or "").strip()
            if label not in {"0", "1"}:
                errors.append(f"{lost_id}: invalid match label {label!r}; expected 0 or 1")
                continue
            labels.append(label)
            if label == "1" and basis != "constructed_positive":
                errors.append(f"{lost_id}: positive pair must have label_basis 'constructed_positive'")
            if label == "0" and not basis.startswith("assumed_"):
                errors.append(f"{lost_id}: negative pair must have an assumed label_basis")
        if labels.count("1") != 1 or labels.count("0") != 2:
            errors.append(
                f"{lost_id}: expected one positive and two negatives, "
                f"found {labels.count('1')} positive and {labels.count('0')} negatives"
            )

    pair_lost_ids = set(pairs_by_lost)
    pair_found_ids = set(found_ids)
    manifest_lost_ids = {}
    manifest_found_ids = {}
    actual_pair_counts = {}
    for name in ("development", "test"):
        partition = split["splits"][name]
        lost_values = partition.get("lost_ids")
        found_values = partition.get("found_ids")
        if not isinstance(lost_values, list) or not all(isinstance(value, str) for value in lost_values):
            errors.append(f"{name} split lost_ids must be a list of strings")
            lost_values = []
        if not isinstance(found_values, list) or not all(isinstance(value, str) for value in found_values):
            errors.append(f"{name} split found_ids must be a list of strings")
            found_values = []
        if len(lost_values) != len(set(lost_values)):
            errors.append(f"{name} split contains duplicate lost IDs")
        if len(found_values) != len(set(found_values)):
            errors.append(f"{name} split contains duplicate found IDs")
        lost_ids = set(lost_values)
        found_ids = set(found_values)
        manifest_lost_ids[name] = lost_ids
        manifest_found_ids[name] = found_ids

        expected_found_ids = {
            (pair.get("found_report_id") or "").strip() for pair in pairs
            if (pair.get("lost_report_id") or "").strip() in lost_ids
            and (pair.get("found_report_id") or "").strip()
        }
        unknown_lost_ids = lost_ids - pair_lost_ids
        if unknown_lost_ids:
            errors.append(f"{name} split contains lost IDs absent from the pair table")
        if found_ids != expected_found_ids:
            errors.append(f"{name} split found_ids do not match the pair table")

        actual_pair_counts[name] = sum(
            (pair.get("lost_report_id") or "").strip() in lost_ids for pair in pairs
        )
        recorded_count = partition.get("pair_count")
        if type(recorded_count) is not int or recorded_count != actual_pair_counts[name]:
            errors.append(
                f"{name} pair_count is {recorded_count!r}; "
                f"pair table has {actual_pair_counts[name]} rows"
            )

    if manifest_lost_ids["development"] & manifest_lost_ids["test"]:
        errors.append("lost IDs appear in both development and test splits")
    if manifest_found_ids["development"] & manifest_found_ids["test"]:
        errors.append("found IDs appear in both development and test splits")
    if manifest_lost_ids["development"] | manifest_lost_ids["test"] != pair_lost_ids:
        errors.append("development and test lost IDs do not cover the pair table")
    if manifest_found_ids["development"] | manifest_found_ids["test"] != pair_found_ids:
        errors.append("development and test found IDs do not cover the pair table")

    if errors:
        raise ValueError("Delhi pair validation failed:\n- " + "\n- ".join(errors))

    return {
        "lost_claims": len(pairs_by_lost),
        "pairs": len(pairs),
        "development_pairs": actual_pair_counts["development"],
        "test_pairs": actual_pair_counts["test"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=Path, default=PAIRS, help="generated labelled pairs CSV")
    parser.add_argument("--split", type=Path, default=SPLIT, help="generated split JSON")
    args = parser.parse_args()
    counts = validate(args.pairs, args.split)
    print("Delhi pair validation passed: " + json.dumps(counts, sort_keys=True))


if __name__ == "__main__":
    main()
