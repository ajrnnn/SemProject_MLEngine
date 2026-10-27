# Dataset sources and boundaries

## Current real-data source and constructed-label experiment

The current notebook uses the [Delhi Metro Lost and Found dataset on Kaggle](https://www.kaggle.com/datasets/forgetabhi/delhi-metro-lost-and-found-dataset), published by `forgetabhi` and attributed there to Delhi Metro Rail Corporation. The local original is `data/raw/delhi/delhi_lost_and_found.csv`, SHA-256 `38a91688e2ff5acaf1261e8893d006f254cdfd9597d48bc8564a9573f1bf475a`. It has **13,713 real found-item rows**, with `item_name`, `description`, `item_quantity`, `station_name`, `receiving_date`, and `receiving_time`. It does not contain corresponding lost claims, returned-item confirmations, or photos. Confirm current source terms before redistributing the CSV.

`scripts/prepare_delhi_data.py` preserves the raw file and all rows, counts exact duplicates (zero) and missing values (8,208 descriptions; 10,511 quantities), collapses whitespace in a generated copy, adds casefolded text, and parses dates and times. It writes `data/processed/cleaned_items.csv` and a non-sensitive audit at `data/processed/delhi_preprocessing_report.json`. The audit also measures distinct source station strings, distinct whitespace-normalized strings, case-folded strings, and collision groups. In the observed source, all 13,713 station values are non-empty; the 229 distinct source strings remain 229 after whitespace cleanup and case-folding, although 44 rows had whitespace changed. There were zero whitespace or case-fold collision groups, so no semantic station alias mapping is applied: nearby or similarly named stations are not proven equivalent by these records. `station_name` is the receiving station recorded by the source; we do not assert it is the exact loss location. No original colour, brand or model columns exist, so these are left absent.

`scripts/create_delhi_experiment.py` uses seed 42. It selects 120 original found rows across ten frequent item names, creates one **fictional lost claim** per selected row, and makes 360 pair labels: 120 positives by construction, 120 assumed same-name negatives, and 120 assumed other-name negatives. Its generated files are `data/processed/synthetic_delhi_lost_claims.csv`, `data/processed/delhi_labelled_pairs.csv`, `data/processed/delhi_modelling_pairs.csv`, and `data/processed/delhi_split.json`. Dates and some locations in fictional claims are invented. Colour remains empty. A different found row is **not proof of a different physical item**, so the negative labels need real review before any field claim. The derived row-level files and model outputs are ignored by Git, just like the raw CSV, because found descriptions can contain personal details.

The current notebook uses this **real found-item source plus synthetic claims and constructed labels**. Its held-out results test only this academic pairing exercise. The four `delhi_*.png` figures contain aggregate EDA counts. The older synthetic campus data and results below are retained as a separate baseline; they are not real reports.

## Data used by the current model

| File | Origin and purpose | What we changed | Limits |
|---|---|---|---|
| `data/raw/campus/synthetic_campus_reports.csv` | 46 **synthetic** lost/found campus reports already in the original project repository. They are examples, not records collected from Strathmore students. The original author and review process are not documented. | The raw file stays unchanged. Six rows have an extra empty CSV field; `scripts/prepare_campus_data.py` repairs the column shift in `data/processed/synthetic_campus_reports.csv`. Text standardisation happens when features are calculated. | A designed sample cannot tell us how often item types, wording, or mistakes occur on campus. |
| `data/raw/campus/labelled_campus_pairs.csv` | 32 designed lost/found pairs already in the repository: 14 `match`, 10 `non_match`, and 8 `plausible`. The original label creator/reviewer is not documented. | The original three-way label is retained. The model's table maps `match` to 1 and both other labels to 0. We also calculate a sensitivity check with `plausible` excluded. | `plausible` means unconfirmed, not proven different. Labels need independent review before real-world claims. |

The two synthetic source files are part of this project; no external dataset licence is asserted for them. They are separate from real reports, which would require consent and access controls. The notebook shows the raw files, cleaning, derived features, and measured results. Generated files under `data/processed/` and `results/` can be recreated from the two tracked CSVs.

## Earlier Delhi exploration and source caution

An earlier version explored the same Delhi dataset but kept it separate from the classifier. The current notebook now uses it as a real found-item source for a **synthetic pairing experiment**; this does not add verified real lost/found labels. The old workbook and exploration files remain in Git history. The earlier dataset note reported Apache 2.0 for the Kaggle listing, but check the current source terms before reusing the data. A fresh clone requires a separate Delhi download.

## Images are future work

The [Roboflow Lost and Found dataset, version 2](https://universe.roboflow.com/rnomo/lost-and-found-nlb4x-e6ayk/dataset/2) is an **object-detection** dataset, not a set of verified photos of the same lost and found item. Its source page lists 4,546 images and CC BY 4.0. No images or annotations from it are included here, and no image model has been trained or evaluated in this repository. If the team later uses it, cite the creator, follow the licence, inspect the downloaded annotations, and define exactly what detection contributes to matching. To evaluate image matching, first collect consented photos with stable physical-item IDs and independent pair labels.

## Splits and leakage

`scripts/split_campus_data.py` uses seed 42 and groups all candidates for one lost report together. The development set has 24 pairs from 10 lost reports; the held-out test has 8 pairs from 4 different lost reports. Found IDs do not cross those partitions. Grouped cross-validation is applied only to development. This reduces repeated-description leakage, but the small synthetic test is still only a prototype check.
