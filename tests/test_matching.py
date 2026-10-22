from matching_system.data_loader import load_labelled_pairs, load_reports
from matching_system.evaluation import evaluate
from matching_system.matcher import rank_candidates
from scripts.prepare_campus_data import prepare

prepare()
REPORTS = "data/processed/synthetic_campus_reports.csv"


def test_known_backpack_match_ranks_first():
    reports = load_reports(REPORTS)
    lost = next(report for report in reports if report.report_id == "lost-001")
    found_reports = [report for report in reports if report.report_type == "found"]

    candidates = rank_candidates(lost, found_reports, limit=3, min_score=0)

    assert candidates[0].found_report_id == "found-001"
    assert candidates[0].requires_human_verification is True


def test_contradictory_colour_is_explained():
    reports = load_reports(REPORTS)
    lost = next(report for report in reports if report.report_id == "lost-004")
    found = next(report for report in reports if report.report_id == "found-012")

    candidate = rank_candidates(lost, [found], limit=1, min_score=0)[0]

    assert any("colour" in conflict for conflict in candidate.conflicting_details)


def test_evaluation_metrics_are_measurable():
    reports = load_reports(REPORTS)
    labels = load_labelled_pairs("data/raw/campus/labelled_campus_pairs.csv")

    metrics = evaluate(reports, labels, k=3)

    assert 0 <= metrics["precision_at_k"] <= 1
    assert 0 <= metrics["recall_at_k"] <= 1
    assert 0 <= metrics["mean_reciprocal_rank"] <= 1
