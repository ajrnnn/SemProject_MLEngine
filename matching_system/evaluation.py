from __future__ import annotations

from collections import defaultdict

from .matcher import rank_candidates
from .models import LabelledPair, Report


def evaluate(reports: list[Report], labels: list[LabelledPair], k: int = 3) -> dict[str, object]:
    lost_reports = [report for report in reports if report.report_type == "lost"]
    found_reports = [report for report in reports if report.report_type == "found"]
    true_matches: dict[str, set[str]] = defaultdict(set)
    labelled_lookup: dict[tuple[str, str], str] = {}

    for pair in labels:
        labelled_lookup[(pair.lost_report_id, pair.found_report_id)] = pair.label
        if pair.label == "match":
            true_matches[pair.lost_report_id].add(pair.found_report_id)

    precision_values: list[float] = []
    recall_values: list[float] = []
    reciprocal_ranks: list[float] = []
    false_positives: list[dict[str, object]] = []
    unlabelled_candidates: list[dict[str, object]] = []

    for lost in lost_reports:
        ranked = rank_candidates(lost, found_reports, limit=k, min_score=0)
        predicted_ids = [candidate.found_report_id for candidate in ranked[:k]]
        correct_ids = true_matches.get(lost.report_id, set())
        hits = [found_id for found_id in predicted_ids if found_id in correct_ids]
        precision_values.append(len(hits) / k)
        recall_values.append(len(hits) / len(correct_ids) if correct_ids else 0.0)

        reciprocal_rank = 0.0
        for index, found_id in enumerate(predicted_ids, start=1):
            if found_id in correct_ids:
                reciprocal_rank = 1 / index
                break
        reciprocal_ranks.append(reciprocal_rank)

        for candidate in ranked[:k]:
            label = labelled_lookup.get((lost.report_id, candidate.found_report_id), "unlabelled")
            if label != "match":
                entry = {
                        "lost_report_id": lost.report_id,
                        "found_report_id": candidate.found_report_id,
                        "score": candidate.score,
                        "label": label,
                    }
                (unlabelled_candidates if label == "unlabelled" else false_positives).append(entry)

    count = len(lost_reports) or 1
    return {
        "precision_at_k": round(sum(precision_values) / count, 3),
        "recall_at_k": round(sum(recall_values) / count, 3),
        "mean_reciprocal_rank": round(sum(reciprocal_ranks) / count, 3),
        "false_positives": false_positives,
        "unlabelled_candidates": unlabelled_candidates,
        "evaluated_lost_reports": len(lost_reports),
        "metric_caveat": "Unlabelled pairs are unknown; precision_at_k assumes only intended 'match' labels are positive.",
    }

