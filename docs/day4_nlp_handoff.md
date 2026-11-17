# Day 4 NLP handoff

The current prototype ranks **possible** found reports from item names and descriptions. It does not establish a same-item link, ownership, or permission to release an item. The included corpus and evaluation labels are synthetic.

## Text preparation and ranking

`normalize_report_text` case-folds text, changes hyphens and punctuation into spaces, collapses whitespace, and keeps word characters. `TfidfRanker._text` concatenates `item_name` and `description`; category, location, date, contact details and ID fields are not separately added. The vectorizer uses `TfidfVectorizer(ngram_range=(1, 2), strip_accents="unicode")` with scikit-learn defaults for token pattern, term frequency, inverse document frequency and L2 normalization. It fits on **found** reports only. A lost query is transformed with that fixed vocabulary, then cosine similarity sorts candidates. Scores are rounded to six decimals; ties sort by `report_id`. Up to five positive-overlap candidates are returned. `min_similarity` is an optional lexical cutoff, not a calibrated match threshold.

The loader selects only explicit general-item columns. It does not inspect free text for embedded personal information. The local preview API now rejects common email-address patterns, phone-like digit sequences, and values following common student-ID, national-ID, ID-number, and passport labels in submitted item names, descriptions, categories, and locations. This is a narrow obvious-pattern safeguard, not a general PII detector; it can miss unusual formats and other sensitive content, and may reject benign text that resembles an ID or phone number. It does not change the loader or make arbitrary real reports safe to submit. Remove contact details and full private IDs from descriptions and names **before** importing data. A separate authorized and human-reviewed intake step is required for real data. The local preview API uses a fixed synthetic inventory and does not persist submitted reports.

## Rebuild the found corpus

From the repository root after installing `requirements.txt`:

```powershell
python -m scripts.rebuild_nlp_index
python -m scripts.rebuild_nlp_index data/fixtures/day3/demo_reports.csv
```

Both commands read the same included fixture and report found-record and vocabulary counts without printing descriptions or tokens. For a later permitted, validated CSV with the standard `TextReport` column names, pass its path to the second command. This checks that the inventory can be loaded and fitted; the index is in memory only. The live pipeline must call `MatchingPipeline.replace_inventory(found_reports)` after an inventory change, or restart its process with a new source. The current API always loads the bundled fixture at startup; the command does **not** update that running API. No real-data hot reload or persistent index exists yet.

## Known failure cases

| Case | Current behavior | Staff interpretation |
| --- | --- | --- |
| Different wording with no shared TF-IDF terms | Empty result | Ask for more details or search manually; this is not proof of no counterpart. |
| Similar-item distractor | May rank highly despite a category conflict | Read the agent's fact trace and inspect the item; lexical overlap is not identity. |
| Missing or broad category, location or date | Agent marks unknown or ambiguous | Request or verify details; do not infer agreement. |
| Different locations | Agent flags a conflict but retains the candidate | Inspect movement and chronology; location alone does not disprove a match. |
| Sparse or empty item text | No useful lexical candidate | Obtain a clearer description. |
| New found item after process startup | Not indexed until `replace_inventory` or process restart | Rebuild before relying on the preview. |
| Embedded personal data in free text | Preview rejects some obvious email, phone-like and labeled-ID patterns; loader and vectorizer do not screen arbitrary text | Remove it during authorized intake review; the API pattern guard is not a substitute and unreviewed real data must not be used. |

Run `python -m unittest discover -s tests -p "test_*.py"` and `python -m scripts.demo_day3` for the synthetic checks. The frozen evaluation and its limits are in `docs/day3_evaluation_evidence.md`. Real-data Recall@5 and MRR@5 remain pending verified same-item labels and a grouped holdout.
