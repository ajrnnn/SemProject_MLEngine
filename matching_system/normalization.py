from __future__ import annotations

import re


SYNONYMS = {
    "blk": "black",
    "dark": "black",
    "dark blue": "navy",
    "grey": "gray",
    "transparent": "clear",
    "zip": "zipper",
    "math": "calculus",
    "notebook computer": "laptop",
    "school bag": "backpack",
    "bag": "backpack",
    "sweatshirt": "hoodie",
    "transit": "bus",
    "type c": "usb c",
    "usb-c": "usb c",
    "upper left": "top left",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "at",
    "for",
    "has",
    "have",
    "in",
    "inside",
    "is",
    "left",
    "my",
    "near",
    "of",
    "on",
    "the",
    "to",
    "with",
}


def normalize_text(value: str | None) -> str:
    text = (value or "").lower()
    text = text.replace("-", " ")
    for source, target in sorted(SYNONYMS.items(), key=lambda item: len(item[0]), reverse=True):
        text = re.sub(rf"\b{re.escape(source)}\b", target, text)
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(value: str | None) -> set[str]:
    return {token for token in normalize_text(value).split() if token and token not in STOPWORDS}


def normalize_scalar(value: str | None) -> str:
    return normalize_text(value)


def split_features(value: str | tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        values = value
    elif isinstance(value, list):
        values = tuple(value)
    else:
        values = tuple(part.strip() for part in value.split(";"))
    return tuple(normalize_text(item) for item in values if normalize_text(item))

