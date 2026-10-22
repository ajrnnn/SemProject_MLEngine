from __future__ import annotations

from datetime import timedelta

from .models import MatchCandidate, Report
from .normalization import normalize_scalar, tokenize
from .image_matching import cosine_similarity


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def compatible_text(left: str, right: str) -> bool:
    return bool(left and right and normalize_scalar(left) == normalize_scalar(right))


def time_score(lost: Report, found: Report) -> float:
    if not lost.reported_at or not found.reported_at:
        return 0.0
    delta = abs(found.reported_at - lost.reported_at)
    if delta <= timedelta(hours=1):
        return 1.0
    if delta <= timedelta(hours=6):
        return 0.7
    if delta <= timedelta(days=1):
        return 0.4
    return 0.0


def score_pair(lost: Report, found: Report, image_embeddings: dict[str, tuple[float, ...]] | None = None) -> MatchCandidate:
    shared: list[str] = []
    conflicts: list[str] = []
    missing: list[str] = []

    lost_text = tokenize(" ".join([lost.description, " ".join(lost.distinctive_features)]))
    found_text = tokenize(" ".join([found.description, " ".join(found.distinctive_features)]))
    text_overlap = jaccard(lost_text, found_text)

    score = 35 * text_overlap

    for field_name, weight in [
        ("category", 15),
        ("brand", 10),
        ("model", 10),
        ("colour", 10),
        ("material", 5),
    ]:
        lost_value = normalize_scalar(getattr(lost, field_name))
        found_value = normalize_scalar(getattr(found, field_name))
        if lost_value and found_value and lost_value == found_value:
            score += weight
            shared.append(f"{field_name}: {lost_value}")
        elif lost_value and found_value and lost_value != found_value:
            score -= min(weight + 5, 20)
            conflicts.append(f"{field_name}: lost has {lost_value}, found has {found_value}")
        else:
            missing.append(field_name)

    lost_features = set(lost.distinctive_features)
    found_features = set(found.distinctive_features)
    feature_overlap = jaccard(lost_features, found_features)
    if feature_overlap:
        score += 15 * feature_overlap
        shared.extend(sorted(lost_features & found_features))
    elif lost_features or found_features:
        missing.append("distinctive feature overlap")

    location_overlap = jaccard(tokenize(lost.location), tokenize(found.location))
    if location_overlap:
        score += 10 * location_overlap
        shared.append("nearby location wording")
    else:
        missing.append("location agreement")

    score += 5 * time_score(lost, found)

    if image_embeddings and lost.image_reference and found.image_reference:
        left = image_embeddings.get(lost.image_reference)
        right = image_embeddings.get(found.image_reference)
        if left is not None and right is not None:
            similarity = cosine_similarity(left, right)
            if similarity > 0 and not conflicts:
                score += min(10.0, 10.0 * similarity)
                shared.append("supporting image similarity")

    score = round(max(0.0, min(100.0, score)), 2)
    explanation = build_explanation(score, shared, conflicts, missing)
    return MatchCandidate(
        found_report_id=found.report_id,
        score=score,
        shared_characteristics=tuple(dict.fromkeys(shared)),
        conflicting_details=tuple(dict.fromkeys(conflicts)),
        missing_information=tuple(dict.fromkeys(missing)),
        explanation=explanation,
    )


def build_explanation(score: float, shared: list[str], conflicts: list[str], missing: list[str]) -> str:
    if conflicts:
        return f"Score {score}: useful similarities exist, but explicit contradictions require caution."
    if score >= 60:
        return f"Score {score}: several description and attribute details agree; send for human verification."
    if score >= 35:
        return f"Score {score}: some evidence agrees, but important details are missing."
    return f"Score {score}: evidence is weak; do not treat as a strong match."


def rank_candidates(
    lost: Report,
    found_reports: list[Report],
    limit: int = 5,
    min_score: float = 30.0,
    image_embeddings: dict[str, tuple[float, ...]] | None = None,
) -> list[MatchCandidate]:
    candidates = [score_pair(lost, found, image_embeddings) for found in found_reports if found.report_type == "found"]
    candidates.sort(key=lambda item: item.score, reverse=True)
    return [candidate for candidate in candidates if candidate.score >= min_score][:limit]

