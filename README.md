# Strathmore Lost & Found: NLP matching prototype

This repository now has two distinct parts: a **text-first matching prototype** under development and the retained **Logistic Regression coursework experiment**. The prototype ranks found reports for staff to review; it does not decide ownership or authorize handover.

## Current direction and status

The intended flow is:

```text
lost report → TF-IDF candidate retrieval → knowledge-based evidence check
            → staff-workflow recommendation → possible matches for staff review
```

NLP retrieves candidates from item names and descriptions. The matching agent compares available category, location and date facts and records agreement, conflict or unknown with rule and reason codes. The workflow agent routes conflicts for inspection, missing details for follow-up, and complete evidence for staff review; it never approves ownership or release. Text similarity is lexical evidence, **not a probability that two reports concern the same item**.

| Component | Current status |
| --- | --- |
| CSV field adapter, text normalization and TF-IDF ranking | Implemented in `matching_system/nlp_retrieval.py`; takes a replaceable found-report inventory. |
| Matching and staff-workflow agents | Implemented as separately testable Python modules and connected to a local synthetic API preview; not connected to a mobile app. |
| Data for development | 46 synthetic campus reports, 32 designed pairs and three additional synthetic queries. No verified real lost/found pairs are available here. |
| Real-case evaluation | Pending permitted reports and independently reviewed same-item links. No campus matching accuracy is claimed. |

The currently reviewed facts are limited to the fields on `TextReport`. Category disagreement is **review evidence**, not an automatic exclusion; different locations can still describe the same item. Missing facts are unknown. The rules are explicit constants with stable IDs; a separately managed knowledge-base file remains future work. The local ranker-to-agents-to-API path is integrated.

## Run the prototype

Use Python 3.11 or newer. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
.\.venv\Scripts\python.exe -m scripts.demo_day3
.\.venv\Scripts\python.exe -m uvicorn matching_system.api:app --host 127.0.0.1 --port 8000
```

On macOS or Linux, activate `.venv` and use `python` in place of the Windows executable. The retrieval component needs `scikit-learn`, already listed in `requirements.txt`.

The local API serves a synthetic found-item inventory from `data/fixtures/day3/demo_reports.csv`. Open `http://127.0.0.1:8000/docs` and try `POST /preview/matches` with:

```json
{
  "item_name": "Metal water bottle",
  "description": "Blue bottle with a scratched lid",
  "category_id": "metal_water_bottle",
  "location_id": "msb",
  "event_date": "2026-11-10",
  "limit": 3
}
```

Each candidate includes a plain-language `explanation` alongside the structured facts, `rule_ids`, `reason_codes`, `rule_trace` and workflow action. The preview rejects obvious email, phone-like number, and common labeled private-ID patterns in its text fields; this limited check is not a general PII detector and does not make arbitrary real reports safe to submit. A candidate excerpt looks like:

```json
{
  "explanation": "Facts: category agrees; location differs; event date agrees. Staff should review the conflicting details. Text similarity is lexical evidence, not a probability. Ownership is unverified; release is not authorized.",
  "rule_ids": ["MA-R001", "MA-R005", "MA-R007", "MA-R010"],
  "reason_codes": ["CATEGORY_AGREEMENT", "LOCATION_DIFFERENCE_NON_DISPOSITIVE", "EVENT_DATE_COMPATIBLE", "TEXT_SIMILARITY_RECORDED"],
  "workflow": {
    "action": "review_conflicts",
    "ownership_approved": false,
    "release_authorized": false
  }
}
```

The explanation uses only fixed fact labels and evidence states; it does not repeat report text or field values. It states the next staff action and clarifies that similarity is not a probability and that ownership/release are not determined. `GET /health` confirms synthetic-preview mode. Requests are not saved; private ID fields are rejected and validation errors do not echo rejected values. Real intake still requires authorized access, human privacy review, and removal/minimization of personal information. An empty result means no lexical candidate in this fixture inventory, not proof that the item does not exist. The [Day 3 pipeline](matching_system/pipeline.py) composes the ranker and both agents; the [Friday knowledge-agent/API handoff](docs/friday_knowledge_agents_api_handoff.md) documents exact facts, rules, traces, API schemas and privacy limits. The [demo notes](docs/day3_demo.md) record inspected cases and limits.

The modules can be composed without a server:

```python
from matching_system.nlp_retrieval import TextReport, TfidfRanker
from matching_system.matching_agent import assess_candidate
from matching_system.staff_workflow_agent import recommend_staff_workflow

lost = TextReport("l1", "lost", "blue bottle with scratched lid", item_name="Bottle")
found = TextReport("f1", "found", "scratched blue bottle", item_name="Bottle")
ranked = TfidfRanker([found]).rank(lost)
if ranked:
    assessment = assess_candidate(lost, found, ranked[0]["text_similarity"])
    workflow = recommend_staff_workflow(assessment)
    print(assessment.to_dict(), workflow.to_dict())
```

`load_text_reports_csv(path, columns=...)` maps future CSV columns explicitly into `TextReport`. It copies only selected general-item fields and rejects private ID-number fields in the mapping. The TF-IDF index is fitted on found-report text; call `replace_inventory(found_reports)` when the inventory changes. `rank(..., min_similarity=...)` can apply a lexical cutoff, but that value is not a calibrated match threshold. The [NLP handoff](docs/nlp_day1_handoff.md) defines the module boundary for integration.

For the exact text preparation, TF-IDF settings, rebuild command and failure cases, see the [Day 4 NLP handoff](docs/day4_nlp_handoff.md).

## Data and evaluation

The tracked campus reports and pair labels are **synthetic**. The [Day 1 audit](docs/day1_data_audit.md) and [fixture ledger](data/fixtures/day1/fixture_ledger.csv) record provenance and pending review. In the new prototype, `plausible` is treated as **uncertain**, not a verified non-match. The three [extra queries](data/fixtures/day1/synthetic_queries.csv) check wording variation, a similar item and an absent counterpart. They are engineering fixtures, not real-campus evidence.

The [real report template](data/templates/day1/real_reports.csv), [verified pair template](data/templates/day1/verified_pairs.csv) and [JSON intake template](data/templates/day1/intake.json) are empty by design. When permitted data arrives:

1. Record its source, access basis and reviewers; remove unnecessary personal details from model text.
2. Map report fields into the general-item contract and validate unique IDs and pair references.
3. Verify same-item links and different-item labels independently; keep unresolved pairs uncertain.
4. Split by physical item or report group before tuning, rebuild the found-item index and evaluate Recall@5, mean reciprocal rank, no-match behavior and inspected errors on held-out real queries.

A found-only dataset or fictional lost claims can exercise ingestion but cannot establish matching accuracy. ID numbers require a separate restricted exact-match workflow and must not enter the general-item NLP corpus.

## Earlier CAT 2 classification experiment

The [coursework notebook](notebooks/LogisticRegression_Base.ipynb) remains available as the assessed Logistic Regression baseline. It uses 13,713 Delhi Metro **found-item** records for cleaning and exploratory analysis, then creates 120 fictional lost claims and 360 constructed pairs for an offline classification exercise. Its held-out precision 0.971, recall 0.944 and F1 0.958 describe those constructed labels only. The Delhi source has no verified lost/found links or handovers, and different source rows are not proof of different physical items.

The older campus classifier uses 32 designed pairs and historically maps `plausible` to class 0, with an exclusion sensitivity check. That assumption belongs to the coursework experiment; the NLP prototype keeps uncertain cases separate. Neither experiment measures performance on verified campus incidents.

To reproduce the Delhi notebook, obtain the raw CSV as described in [dataset sources](docs/dataset_sources.md), place it at `data/raw/delhi/delhi_lost_and_found.csv`, verify its documented hash, run `python -m scripts.create_delhi_experiment`, then run all cells in the notebook. The raw Delhi CSV and row-level derivatives are Git-ignored because descriptions may contain personal information. The historical synthetic campus model can be run with `python -m scripts.run_model`.

## Next integration steps

Review the fixture labels and demo errors, validate the intake contract with permitted real reports and verified pairs, and test the full path before a field pilot. Integrate with a mobile client only after server persistence, authentication and data handling are stable. Keep every output framed as a possible-match suggestion requiring staff verification. See [team contributions](docs/contributions.md) for the repository history.
