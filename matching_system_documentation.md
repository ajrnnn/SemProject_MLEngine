# AI-Assisted Campus Lost and Found Matching System

## 1. Stage A Objective

The immediate goal is to define and test the data foundation for a text-based lost-and-found matching engine. The system should compare a lost-item report with possible found-item reports, rank likely candidates, and explain the evidence for and against each candidate.

At this stage, the system must not make ownership decisions. A high score should mean "worth human review", not "this item belongs to the claimant".

The current real-world reference file is `data/raw/delhi/delhimetrorail.csv`. It contains 13,713 found-item records with these fields:

- `item_name`
- `description`
- `item_quantity`
- `station_name`
- `receiving_date`
- `receiving_time`

That file is useful for studying messy lost-and-found wording, but it is not ideal as the first labelled evaluation dataset because it has no paired lost reports and no confirmed match labels. For Stage A, the project should use a small synthetic campus dataset where the correct relationships are known.

## 2. Problem Definition

The matching engine receives:

- One lost-item report.
- A collection of found-item reports.

It returns:

- The top candidate found reports when enough evidence exists.
- Shared characteristics such as category, colour, brand, model, location, and distinctive features.
- Contradictions such as different colours, brands, models, or categories.
- Missing information that prevents a confident recommendation.
- A recommendation that a human reviewer verifies the match.

The hard part is that reports may use different wording for the same idea. For example, "black backpack" and "dark school bag" may describe the same object. Reports may also be incomplete, misspelled, vague, or misleadingly similar.

## 3. Report Schema

Use one common schema for both lost and found reports:

| Field | Purpose |
| --- | --- |
| `report_id` | Unique ID such as `lost-001` or `found-001`. |
| `report_type` | Either `lost` or `found`. |
| `description` | Free-text user description. This is the main text-matching input. |
| `category` | Normalized item type, such as `backpack`, `phone`, `wallet`, or `charger`. |
| `brand` | Optional brand, such as `Apple`, `HP`, or `Casio`. |
| `model` | Optional model, such as `iPhone 13` or `fx-991EX`. |
| `colour` | Main visible colour. Use one value for the prototype. |
| `material` | Optional material, such as `leather`, `metal`, `plastic`, or `fabric`. |
| `distinctive_features` | Semicolon-separated special details such as `red zipper; calculus notebook`. |
| `location` | Campus location where the item was lost or found. |
| `reported_at` | ISO-8601 timestamp with timezone. |
| `status` | Current report status, initially `active`. |
| `image_reference` | Optional image path or URL for later stages. Empty in Stage A. |

Sensitive information should stay outside this matching schema. Do not expose phone numbers, student IDs, personal addresses, identity-document numbers, or private proof-of-ownership answers in public match results.

Example report:

```json
{
  "report_id": "lost-001",
  "report_type": "lost",
  "description": "Black Adidas backpack with red zipper and small calculus notebook inside",
  "category": "backpack",
  "brand": "Adidas",
  "model": null,
  "colour": "black",
  "material": "fabric",
  "distinctive_features": ["red zipper", "calculus notebook"],
  "location": "main library second floor",
  "reported_at": "2026-10-07T14:30:00+03:00",
  "status": "active",
  "image_reference": null
}
```

## 4. Stage A Dataset Files

Two synthetic CSV files have been created for the first text-matching prototype:

- `data/raw/campus/synthetic_campus_reports.csv`
- `data/raw/campus/labelled_campus_pairs.csv`

### `data/raw/campus/synthetic_campus_reports.csv`

This file contains 46 reports:

- 14 lost reports.
- 32 found reports.

The examples cover common campus items:

- Backpack
- Laptop
- Phone
- Water bottle
- Wallet
- Umbrella
- Earbuds
- Notebook
- Keys
- Clothing
- Calculator
- Jewellery
- Charger
- Book

The dataset intentionally includes:

- Exact or near-exact matches.
- Paraphrases, such as `dark school bag` versus `black backpack`.
- Spelling and wording variants, such as `Blk` and `black`, `gray` and `grey`, `USB-C` and `type C`.
- Missing fields.
- Generic descriptions.
- Same-category distractors.
- Contradictory attributes, such as wrong colour, brand, model, or material.
- Nearby but not identical locations.
- Close report times.

### `data/raw/campus/labelled_campus_pairs.csv`

This file contains 32 labelled lost-found pairs:

- 14 `match` rows.
- 8 `plausible` rows.
- 10 `non_match` rows.

Labels mean:

| Label | Meaning |
| --- | --- |
| `match` | The found report should be treated as the correct target for the lost report. |
| `plausible` | The found report shares some evidence but is not confirmed as the correct match. It is useful for testing ranking quality and false-positive risk. |
| `non_match` | The found report should not be returned as a strong candidate, usually because of a contradiction. |

The `match_type` and `notes` columns explain why each pair was labelled that way.

## 5. Evaluation Approach

For the first text-matching prototype, evaluate each lost report by ranking candidate found reports.

Recommended first metrics:

- **Precision@3:** Of the top three returned candidates, how many are true `match` rows?
- **Recall@3:** Of the true matches, how many appear in the top three?
- **Mean reciprocal rank:** How high does the first correct match appear?
- **False-positive review:** Which `plausible` or `non_match` rows were ranked too highly?
- **No-strong-match behavior:** Whether the system avoids returning strong matches when evidence is weak.

For early testing, treat `match` as the only correct label. Use `plausible` rows as hard distractors, not as successes. They are valuable because they look tempting but should not be treated as confirmed matches.

## 6. Preventing Test Leakage

Do not tune weights or rules by repeatedly looking at the final test labels. A beginner-friendly split can be:

- Development set: about 70% of the lost reports.
- Held-out test set: about 30% of the lost reports.

Use the development set to adjust scoring rules. Use the held-out test set only for final evaluation of that version.

Because this dataset is small, any metric will be unstable. If one additional example changes the score dramatically, that is expected. The first purpose is to catch obvious mistakes, not to prove production accuracy.

## 7. Dataset Limitations

This Stage A dataset is deliberately small and synthetic. Its limitations are:

- It does not represent all campus item types.
- The labels are designed examples, not real confirmed claim outcomes.
- User writing style is simplified compared with production reports.
- It has no images yet.
- It has no multilingual reports.
- It does not include privacy-sensitive proof-of-ownership fields.
- It cannot prove real-world accuracy.

The Delhi Metro CSV can later help test robustness against larger, messier found-item descriptions, but it still needs labelled lost-found pairs before it can support reliable evaluation.

## 8. Current Implementation

The remaining project stages have been scaffolded in code and documented in `STAGES_B_TO_G.md`.

Implemented project files:

- `matching_system/models.py`
- `matching_system/normalization.py`
- `matching_system/data_loader.py`
- `matching_system/matcher.py`
- `matching_system/evaluation.py`
- `matching_system/image_matching.py`
- `matching_system/api.py`
- `run_evaluation.py`
- `tests/test_matching.py`
- `requirements.txt`

The next verification step is to install Python 3.11+ and run:

```powershell
python -m pip install -r requirements.txt
python run_evaluation.py
python -m pytest -q
```

On 14 October 2026, Python 3.14 was available. The six malformed source rows were corrected in a generated copy, the baseline ran, five standard-library pipeline/API/image tests and the three matcher test functions passed. Pytest itself was unavailable because package-registry DNS failed. Current counts and caveats are in `docs/DATASET.md` and `results/baseline_results.json`.
