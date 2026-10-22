# Strathmore Lost and Found AI prototype

## Project objective

Compare one lost-item report with one found-item report and suggest pairs worth human review. A score never establishes ownership; authorised Lost and Found staff must verify a claim before an item is released.

## CAT 2 definition

**AI Application: Classification**

**Algorithm/Approach: Logistic Regression**

The supervised model classifies a report pair as `1 = match` or `0 = non-match`. The CAT 2 workflow is **raw data -> exploration -> cleaning -> EDA -> pair features -> Logistic Regression -> grouped validation -> evaluation**. Start with [LogisticRegression_Base.ipynb](LogisticRegression_Base.ipynb). Its outputs are from the synthetic dataset, not real campus performance.

## Existing baseline and datasets

The manually weighted matcher in `matching_system/matcher.py` is retained as the **Rule-Based Baseline**. It is not trained ML and still powers the small prototype API. The Logistic Regression experiment is offline; the API and Android starter do not use it yet.

`matching_system_testing.ipynb` is a separate engineering notebook. `trial.ipynb` contains earlier exploration and historical outputs; use the CAT 2 notebook for current assessed results.

* `data/raw/campus/synthetic_campus_reports.csv`: 46 synthetic reports, including six malformed source rows repaired in a generated copy.
* `data/raw/campus/labelled_campus_pairs.csv`: 32 designed pairs (14 `match`, 8 `plausible`, 10 `non_match`). The CAT classifier maps `plausible` to class 0 as a coursework assumption and reports an exclusion sensitivity check. Unlabelled pairs remain unknown.
* Delhi Metro: 13,713 real-world *found-item* records for data-quality exploration. The raw CSV is excluded from this branch's new commits because descriptions may contain personal details. Obtain your own copy from the source and place it at `data/raw/delhi/delhimetrorail.csv` before running the full notebook; see `docs/DATASET.md`. It has no verified lost/found pairs and cannot measure matching accuracy.
* Future images: no downloaded Roboflow images, own same-item photographs, image encoder, or measured CLIP result. See `docs/IMAGE_DATASET_GUIDE.md`.

Raw campus inputs are kept unchanged. Keep the Delhi CSV local and do not commit or redistribute it without a privacy review. Generated data goes under `data/processed/`; measured model outputs go under `results/ml/`. Dataset provenance and limits are in `docs/DATASET.md`.

## Run CAT 2

From the repository root, with Python 3.11+:

```powershell
python -m pip install -r requirements.txt
python -m scripts.run_cat2
jupyter notebook LogisticRegression_Base.ipynb
```

The classifier command needs only the tracked campus files. For the full notebook, first download the Delhi Metro CSV as described in `docs/DATASET.md`, save it at `data/raw/delhi/delhimetrorail.csv`, and verify its SHA-256 hash. Run the notebook from first cell to last. `python -m scripts.run_cat2` regenerates the cleaned campus copy, `data/processed/modelling_pairs.csv`, grouped split, predictions, coefficients and `results/ml/validation_metrics.json`. On 22 October 2026, all 11 code cells completed without errors in a local Python environment with the declared dependencies. The four EDA figures rendered in the notebook and were saved under `results/figures/`. A fresh clone still needs the separately obtained Delhi CSV for a full rerun.

To check the original rule-based baseline and available tests:

```powershell
python run_evaluation.py
python -m unittest discover -s tests -p "test_*.py"
python -m pytest -q
uvicorn matching_system.api:app --reload
```

`pytest` is needed for the three function-style tests in `tests/test_matching.py`. The FastAPI endpoints use a static synthetic inventory; `POST /reports` does not save reports. Never expose this prototype publicly with sensitive reports. The `android/` folder is an app scaffold with no sign-in, reporting flow or API integration.

## Current status and limitations

**Implemented:** raw-data preparation, pair features, offline Logistic Regression training and grouped validation, synthetic test evaluation, rule-based matcher and prototype API.

**Partially implemented:** labels have not had independent review; the four EDA figures are verified for the local dataset but depend on the separately obtained Delhi CSV for reproduction.

**Planned:** real-campus evaluation, image pairs and CLIP features, model comparison, durable backend and Android integration.

The held-out check has eight synthetic pairs from four lost reports. Such a small, designed sample cannot support a production accuracy claim. See `docs/CAT2_WORKFLOW.md`, `docs/MODEL_EXPLANATION.md`, and `docs/NEXT_STEPS.md` for the presentation guide and next work.
