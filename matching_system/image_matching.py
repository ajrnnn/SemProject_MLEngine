from __future__ import annotations

import math


def cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    """Compare two already-computed image embeddings, without implying item identity."""
    if not left or len(left) != len(right):
        raise ValueError("Image embeddings must be non-empty and have equal dimensions")
    if not all(math.isfinite(value) for value in (*left, *right)):
        raise ValueError("Image embeddings must contain finite values")
    magnitude = math.sqrt(sum(value * value for value in left) * sum(value * value for value in right))
    if magnitude == 0:
        raise ValueError("Image embeddings must be non-zero")
    return sum(a * b for a, b in zip(left, right)) / magnitude


def image_matching_status() -> dict[str, str]:
    return {
        "stage": "C",
        "status": "not_enabled",
        "reason": "No item images are present in the Stage A dataset.",
        "recommendation": (
            "When images are available, evaluate a pretrained CLIP-style model as supporting evidence only. "
            "Do not use visual similarity alone as proof of ownership."
        ),
    }

