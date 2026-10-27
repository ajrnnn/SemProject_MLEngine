# Dataset sources and boundaries

## Data used by the current model

| File | Origin and purpose | What we changed | Limits |
|---|---|---|---|
| `data/raw/campus/synthetic_campus_reports.csv` | 46 **synthetic** lost/found campus reports already in the original project repository. They are examples, not records collected from Strathmore students. The original author and review process are not documented. | The raw file stays unchanged. Six rows have an extra empty CSV field; `scripts/prepare_campus_data.py` repairs the column shift in `data/processed/synthetic_campus_reports.csv`. Text standardisation happens when features are calculated. | A designed sample cannot tell us how often item types, wording, or mistakes occur on campus. |
| `data/raw/campus/labelled_campus_pairs.csv` | 32 designed lost/found pairs already in the repository: 14 `match`, 10 `non_match`, and 8 `plausible`. The original label creator/reviewer is not documented. | The original three-way label is retained. The model's table maps `match` to 1 and both other labels to 0. We also calculate a sensitivity check with `plausible` excluded. | `plausible` means unconfirmed, not proven different. Labels need independent review before real-world claims. |

The two synthetic source files are part of this project; no external dataset licence is asserted for them. They are separate from real reports, which would require consent and access controls. The notebook shows the raw files, cleaning, derived features, and measured results. Generated files under `data/processed/` and `results/` can be recreated from the two tracked CSVs.

## Earlier external exploration, not model training

An earlier version of this repository explored the [Delhi Metro Lost and Found dataset on Kaggle](https://www.kaggle.com/datasets/forgetabhi/delhi-metro-lost-and-found-dataset), published by `forgetabhi` and attributed there to Delhi Metro Rail Corporation. The older local copy had 13,713 **found-item** rows. It provides no verified lost/found pair labels, so it cannot train or evaluate this pair classifier. Its descriptions may include personal details. The old workbook, exploration notebook, and prepared Delhi files were removed from the current project tree; their Git history still exists. The earlier dataset note reported Apache 2.0 for the Kaggle listing, but check the current source terms before reusing the data. The current notebook does not require a Delhi download.

## Images are future work

The [Roboflow Lost and Found dataset, version 2](https://universe.roboflow.com/rnomo/lost-and-found-nlb4x-e6ayk/dataset/2) is an **object-detection** dataset, not a set of verified photos of the same lost and found item. Its source page lists 4,546 images and CC BY 4.0. No images or annotations from it are included here, and no image model has been trained or evaluated in this repository. If the team later uses it, cite the creator, follow the licence, inspect the downloaded annotations, and define exactly what detection contributes to matching. To evaluate image matching, first collect consented photos with stable physical-item IDs and independent pair labels.

## Splits and leakage

`scripts/split_campus_data.py` uses seed 42 and groups all candidates for one lost report together. The development set has 24 pairs from 10 lost reports; the held-out test has 8 pairs from 4 different lost reports. Found IDs do not cross those partitions. Grouped cross-validation is applied only to development. This reduces repeated-description leakage, but the small synthetic test is still only a prototype check.
