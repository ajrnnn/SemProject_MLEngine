"""Keep each lost report and its labelled found candidates in one split."""

import csv
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 42


def split() -> dict:
    with (ROOT / "data" / "raw" / "campus" / "labelled_campus_pairs.csv").open(encoding="utf-8", newline="") as handle:
        pairs = list(csv.DictReader(handle))
    groups = defaultdict(set)
    for pair in pairs:
        groups[pair["lost_report_id"]].add(pair["found_report_id"])
    lost_ids = sorted(groups)
    random.Random(SEED).shuffle(lost_ids)
    n_test = round(len(lost_ids) * 0.3)
    test_ids = set(lost_ids[:n_test])
    result = {"seed": SEED, "strategy": "Shuffle lost IDs; keep every labelled found candidate with its lost ID", "splits": {}}
    for name, ids in (("development", set(lost_ids) - test_ids), ("test", test_ids)):
        found = set().union(*(groups[item] for item in ids))
        result["splits"][name] = {"lost_ids": sorted(ids), "found_ids": sorted(found), "pair_count": sum(p["lost_report_id"] in ids for p in pairs)}
    if set(result["splits"]["development"]["found_ids"]) & set(result["splits"]["test"]["found_ids"]):
        raise ValueError("Found report spans splits")
    path = ROOT / "data" / "processed" / "campus_split.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(split(), indent=2))
