# Development Stages B to G

This project now has a runnable Python structure for the remaining stages. The matching engine is still a prototype and should be evaluated before any production or Android integration decisions.

## Stage B: Text-Based Matching Prototype

Implemented files:

- `matching_system/models.py`
- `matching_system/normalization.py`
- `matching_system/data_loader.py`
- `matching_system/matcher.py`
- `run_evaluation.py`
- `tests/test_matching.py`

What it does:

- Loads `data/raw/campus/synthetic_campus_reports.csv`.
- Loads `data/raw/campus/labelled_campus_pairs.csv`.
- Validates required CSV columns.
- Normalizes common wording variants such as `blk` to `black`, `grey` to `gray`, `school bag` to `backpack`, and `USB-C` to `usb c`.
- Scores lost-found pairs using:
  - description token overlap,
  - category,
  - brand,
  - model,
  - colour,
  - material,
  - distinctive features,
  - location wording,
  - time proximity.
- Penalizes explicit contradictions.
- Returns ranked candidates with explanations and `requires_human_verification`.

Run:

```powershell
python run_evaluation.py
python -m pytest -q
```

Notebook option:

- Open `matching_system_testing.ipynb`.
- Select a Python 3.11+ kernel.
- Run the cells from top to bottom.

If `python` is unavailable on Windows, install Python 3.11+ and enable "Add python.exe to PATH" during installation.

## Stage C: Image Matching

Implemented file:

- `matching_system/image_matching.py`

Current status:

- The ranker accepts optional precomputed image embeddings and a capped cosine-similarity bonus, but no image encoder, image data or image experiment is available locally.
- The code records the planned approach: use a pretrained CLIP-style model later as supporting evidence only.

Important rule:

Visual similarity can help rank candidates, but it must not prove ownership. Two black backpacks may look similar while still being different physical items.

Future image tasks:

1. Add image paths to `image_reference`.
2. Test image quality, lighting, angle, and background.
3. Compare image-to-image and image-to-text behavior.
4. Keep distinctive text attributes active around image scores.

## Stage D: Hybrid Ranking

Implemented in:

- `matching_system/matcher.py`

The current ranking is hybrid but text-first:

- Text evidence: description and distinctive-feature wording.
- Structured evidence: category, brand, model, colour, material.
- Context evidence: location and time.
- Contradiction penalties: wrong colour, brand, model, material, or category.

Missing fields are not treated as contradictions. For example, if the found report has no brand, that should not be punished as though it conflicts with the lost report.

## Stage E: Evaluation

Implemented in:

- `matching_system/evaluation.py`
- `run_evaluation.py`
- `tests/test_matching.py`

Current metrics:

- Precision@3
- Recall@3
- Mean reciprocal rank
- False positives in the top 3

For evaluation, only `match` labels count as correct. `plausible` labels are treated as hard distractors so the system learns not to over-trust generic similarity.

## Stage F: FastAPI Backend

Implemented file:

- `matching_system/api.py`

Available endpoints:

- `GET /health`
- `GET /reports`
- `POST /matches`
- `POST /reports`

Run:

```powershell
python -m pip install -r requirements.txt
uvicorn matching_system.api:app --reload
```

Example match request:

```json
{
  "lost_report_id": "lost-001",
  "limit": 5,
  "min_score": 30
}
```

The `POST /reports` endpoint is currently a placeholder. It accepts data but does not persist it because database selection should happen after the matching prototype is evaluated.

## Stage G: Android Integration Plan

The Android project is now a starter scaffold; do not connect it to the API until backend persistence and permissions are stable. The Kotlin app should eventually:

- Submit lost reports.
- Submit found reports.
- Upload optional images.
- Request ranked matches from the API.
- Display scores as review signals, not proof.
- Show shared details, conflicts, and missing information.
- Require authorised human confirmation before an item is released.

Recommended Android data classes later:

```kotlin
data class MatchRequest(
    val lostReportId: String,
    val limit: Int = 5,
    val minScore: Double = 30.0
)

data class MatchCandidate(
    val foundReportId: String,
    val score: Double,
    val sharedCharacteristics: List<String>,
    val conflictingDetails: List<String>,
    val missingInformation: List<String>,
    val explanation: String,
    val requiresHumanVerification: Boolean
)
```

## Verified status on 14 October 2026

Python 3.14 is available. The original synthetic CSV has six shifted rows, so run the preparation script (or `run_evaluation.py`, which invokes it) before loading reports. The current baseline and split results are saved under `results/`. Five standard-library pipeline/API/image tests and the three existing matcher tests passed. The `pytest` package could not be installed in this environment because package-registry DNS was unavailable; a normal `python -m pytest -q` run remains outstanding.

Run:

```powershell
python scripts/prepare_campus_data.py
python run_evaluation.py
python -m pytest -q
```

