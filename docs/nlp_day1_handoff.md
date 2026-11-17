# NLP retrieval handoff (Day 1)

`matching_system.nlp_retrieval` is an independent text retrieval component for the new prototype. It does not change the historical Logistic Regression coursework experiment. It ranks found reports by TF-IDF cosine similarity and returns lexical evidence, not a match probability or ownership decision.

## Interface for Alex

Use `TextReport` for both lost queries and found inventory. `TfidfRanker(found_reports).rank(lost_report, limit=5)` returns ordered dictionaries with `found_report_id` and `text_similarity`. Keep knowledge-base facts, conflicts, staff actions and final presentation outside this module. Category, location and event date travel on `TextReport` for that reasoning layer; they do not enter the text vector.

## Interface for Louis

`load_text_reports_csv(path, columns=...)` accepts an explicit mapping from the standard fields (`report_id`, `report_type`, `description`, optional `item_name`, `category_id`, `location_id`, `event_date`) to source CSV columns. It requires report IDs to be unique and rejects private ID-number columns in the mapping. For the existing synthetic campus CSV, map `item_name` to `category` only as a temporary legacy text fallback; record that choice in the fixture ledger. Do not present those fixtures as real-campus validation.

## Rebuild when data arrives

Load the reviewed found-report inventory, construct a new `TfidfRanker`, and query it with lost reports. The vectorizer is fitted only on found-report text, so the index must be rebuilt when the inventory changes. Keep the source and label provenance, perform a grouped holdout by physical item, and evaluate ranking separately. A found-only dataset cannot establish matching accuracy.

Day 2 adds `ranker.replace_inventory(found_reports)`, which refits the index and also accepts an empty inventory. A failed inventory validation leaves the previous index intact. `rank(lost, limit=5, min_similarity=0.0)` accepts up to five results; the optional cosine cutoff is **not calibrated** as a match threshold. An empty result means no text passed this lexical cutoff, not that no physical match exists. Keep the agent's structured evidence and staff review separate from this retrieval decision.

## Run

From this repository root, with the project dependencies installed:

```powershell
python -m unittest tests.test_nlp_retrieval -v
```
