import json
from collections import Counter
from pathlib import Path

from matching_system.data_loader import load_labelled_pairs, load_reports
from matching_system.evaluation import evaluate
from scripts.prepare_campus_data import prepare
from scripts.split_campus_data import split


def main() -> None:
    root = Path(__file__).resolve().parent
    correction = prepare()
    reports = load_reports(root / "data/processed/synthetic_campus_reports.csv")
    labels = load_labelled_pairs(root / "data/raw/campus/labelled_campus_pairs.csv")
    metrics = evaluate(reports, labels, k=3)
    metrics["synthetic_corrections"] = correction
    manifest = split()
    metrics["split"] = {"seed": manifest["seed"], "strategy": manifest["strategy"], "results": {}}
    for name, partition in manifest["splits"].items():
        allowed = set(partition["lost_ids"] + partition["found_ids"])
        portion = [report for report in reports if report.report_id in allowed]
        portion_labels = [pair for pair in labels if pair.lost_report_id in partition["lost_ids"]]
        metrics["split"]["results"][name] = evaluate(portion, portion_labels, k=3)
    results = root / "results"
    results.mkdir(exist_ok=True)
    (results / "baseline_results.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    notes = {(pair.lost_report_id, pair.found_report_id): pair.notes for pair in labels}
    errors = {
        "scope": "Top three among all 32 found reports per synthetic lost report, with no score threshold",
        "labelled_distractor_counts": dict(Counter(item["label"] for item in metrics["false_positives"])),
        "unlabelled_candidate_count": len(metrics["unlabelled_candidates"]),
        "highest_scoring_labelled_distractors": [
            {**item, "label_note": notes[(item["lost_report_id"], item["found_report_id"])]}
            for item in sorted(metrics["false_positives"], key=lambda item: item["score"], reverse=True)[:10]
        ],
    }
    (results / "baseline_error_analysis.json").write_text(json.dumps(errors, indent=2) + "\n", encoding="utf-8")
    print("Evaluation metrics")
    print(f"Precision@3: {metrics['precision_at_k']}")
    print(f"Recall@3: {metrics['recall_at_k']}")
    print(f"Mean reciprocal rank: {metrics['mean_reciprocal_rank']}")
    print(f"False positives in top 3: {len(metrics['false_positives'])}")
    print(f"Unlabelled top-3 candidates: {len(metrics['unlabelled_candidates'])}")
    for item in metrics["false_positives"][:10]:
        print(item)


if __name__ == "__main__":
    main()

