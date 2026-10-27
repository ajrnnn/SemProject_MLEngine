# Strathmore Lost & Found AI

This is the **machine-learning part** of a proposed Strathmore University Lost & Found mobile application. Given one lost-item report and one found-item report, it estimates whether staff should review them as a possible match. It does **not** establish ownership or automatically return an item.

- **AI Application:** Classification
- **Algorithm/Approach:** Logistic Regression
- **Current output:** a match probability and a binary `match` / `non-match` suggestion for each report pair. Several found reports can then be ordered by probability for staff review.

The [main learning notebook](notebooks/LogisticRegression_Base.ipynb) shows the whole process. Small helper modules keep cleaning and feature calculations consistent between the notebook and command-line run.

## Dataset

We use two tracked **synthetic** campus files:

| File | What it contains | Used for |
|---|---|---|
| [`synthetic_campus_reports.csv`](data/raw/campus/synthetic_campus_reports.csv) | 46 lost/found report examples | Exploration, cleaning, and pair features |
| [`labelled_campus_pairs.csv`](data/raw/campus/labelled_campus_pairs.csv) | 32 labelled lost/found pairs: 14 `match`, 10 `non_match`, 8 `plausible` | Training and evaluation |

The raw reports contain six rows with a shifted column caused by an extra empty CSV field. Cleaning writes a corrected **copy** under `data/processed/`; the raw files stay unchanged. `plausible` means an unconfirmed possible match. The binary experiment maps it to class 0, but also checks results with those uncertain rows excluded.

An older Delhi Metro dataset was explored in this project's history. It has found items but no verified lost/found pairs and is **not used** to train or evaluate this model. No image dataset or image model is included. See [dataset sources](docs/dataset_sources.md) for provenance, limitations, and future image-data requirements.

## Repository map

```text
SemProject_MLEngine/
├── README.md
├── requirements.txt
├── data/
│   ├── raw/campus/              # original synthetic CSV files
│   └── processed/               # cleaned reports, pair features, split
├── notebooks/
│   └── LogisticRegression_Base.ipynb
├── matching_system/             # loading, text cleaning, features, model
├── scripts/                     # short commands for each data/model step
├── results/
│   ├── figures/                 # four dataset charts
│   └── ml/                      # predictions, coefficients, measured metrics
├── tests/                       # focused checks of important behavior
└── docs/dataset_sources.md
```

The model code is in [`matching_system/ml_model.py`](matching_system/ml_model.py). [`feature_builder.py`](matching_system/feature_builder.py) turns a pair of reports into numeric inputs. Start with the notebook before reading the helper code.

## Install and run

Use Python 3.11 or newer. From the repository root:

```powershell
git clone https://github.com/nimrod-kobia/SemProject_MLEngine.git
cd SemProject_MLEngine
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m notebook
```

Open `notebooks/LogisticRegression_Base.ipynb` in Jupyter and choose **Run All**. The notebook needs only the two tracked campus CSVs. It shows raw data, correction of six rows, four observations and charts, pair features, training, validation, predictions, and limitations. It saves charts and measured results under `results/`.

To regenerate the table, split, and model results without Jupyter:

```powershell
.\.venv\Scripts\python.exe -m scripts.run_model
```

On macOS/Linux, activate `.venv` with `source .venv/bin/activate` and use `python` in place of the Windows executable path.

## How the model works

```text
Raw campus reports + labelled pairs
    → correct shifted CSV rows
    → compare each lost/found pair using 14 numeric features
    → split by lost-report ID
    → fit StandardScaler + Logistic Regression on development pairs
    → grouped cross-validation and held-out test
    → probabilities, predictions, and error analysis
```

The features compare description words, distinctive details, locations, item attributes, and reported times. A missing attribute produces neither a match nor a conflict. The target `y` is 1 for labelled `match` and 0 for the other two labels; `X` is the feature table. The training cell shows `model.fit(X_train, y_train)` directly.

All candidate pairs belonging to one lost report remain in the same split. This keeps the same lost description from appearing in both training and testing. Scaling is learned inside each training fold before that fold's validation pairs are checked.

## Measured results and example

The held-out check has **8 synthetic pairs**, including four labelled matches. The saved run gives precision **1.00**, recall **0.75**, and F1 **0.857**. Its confusion matrix is `[[4, 0], [1, 3]]` (rows: actual 0/1; columns: predicted 0/1): four true negatives, three true positives, one false negative, and no false positives. These numbers are calculated in the notebook and stored in [`validation_metrics.json`](results/ml/validation_metrics.json). They are **not** a real-campus accuracy estimate.

For example, the held-out pair `lost-008` / `found-019` describes a red spiral economics notebook in nearby rooms. The saved model assigns a match probability of about **0.911**, predicts `match`, and the synthetic label is `match`. The notebook also shows a missed labelled match and an ambiguous `plausible` case. Staff must inspect any suggested pair and verify ownership privately.

## Limits and next work

- Only 32 designed pairs exist, with 8 held out. The labels have not been independently reviewed.
- Mapping `plausible` to 0 is an assumption; the notebook includes a check that excludes those rows.
- There is no real campus field test and no validated photo matching. The trained classifier is offline; the Android app does not use it yet.
- Next: review labels, gather consented campus examples, compare another simple model using the same grouped split and metrics, and integrate tested suggestions into the app with staff verification.

## CAT 2 Assessment Guide

CAT 2 is the **assessment**, not the name of the model or a software component. The brief asks for the following evidence:

| Assessment requirement | Evidence in this repository | Status |
|---|---|---|
| **1. Identify the ML approach and relevant algorithms for the dataset and app output.** | This README's opening and workflow; notebook sections **1, 5–6** explain binary classification, Logistic Regression, inputs, and output. | Repository explanation complete. The required entry in the course's shared spreadsheet must be checked separately. |
| **2. Detail data cleaning from exploration to the final modelling dataset and derive at least four EDA observations.** | Notebook sections **2–5** show raw rows, six shifted records, corrected copy, four calculated observations and charts, and the final pair-feature table. | Complete for the synthetic dataset. |
| **3. Describe the base modelling approach and apply suitable validity measures.** | Notebook sections **5–7** show `X`, `y`, `model.fit`, grouping, cross-validation, held-out metrics, confusion matrix, and examples. | Complete as a small prototype; accuracy beyond this sample remains unverified. |
| **4. Determine further validation methods.** | Notebook section **8** describes label review, real-campus testing, and a fair same-split model comparison. The brief says a description is sufficient at this stage. | Described; comparison is future work. |

The required notebook filename is `LogisticRegression_Base.ipynb`, and the public submission repository is `SemProject_MLEngine`. The group must still check its spreadsheet entry, members' forks, assigned presentation date, and each member's ability to explain the work. Follow the course's rules on permitted AI assistance and authorship.

### Presentation path

1. Open this README and state the problem, dataset, model, and expected app output.
2. Open the main notebook. Show the original rows and the six corrected rows.
3. Explain the four calculated observations and charts.
4. Show one row of pair features, identify `X` and `y`, and point to `model.fit`.
5. Explain why the split and validation are grouped by lost report.
6. Show the held-out confusion matrix, example predictions, and the missed match.
7. State the limitations and how the team would validate further before app integration.
