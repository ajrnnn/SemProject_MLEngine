# Day 2 reproducible SYNTHETIC evaluation

Run python scripts/evaluate_day2_synthetic.py from repository root with project
Python dependencies. Output: results/day2_synthetic_evaluation.json, including
source SHA256 hashes, query splits, relevant IDs and complete top-five rankings.
Base: upstream main d71a908. No raw files or ranker/agent modules are changed.

46 synthetic reports, 32 found inventory entries, 14 lost queries. Designed
match edges form connected physical-item groups. SHA256(group) modulo 3 assigns
test when zero, development otherwise; all variants of an item must retain its
group. This is a fixed prototype split, not a trained-model generalization claim.
The index is fit on the common found-only inventory; test counterpart documents
are deliberately indexed, as required for retrieval. No lost query text is fit.
Uncertain links do not prove identity; adjudicate before any real grouped holdout.

SYNTHETIC results: development n=11 Recall@5=1.0 MRR@5=0.651515;
test n=3 Recall@5=1.0 MRR@5=0.611111; all n=14 Recall@5=1.0
MRR@5=0.642857. Recall averages retrieved relevant / known relevant per query.
MRR@5 averages reciprocal first relevant rank, zero beyond five. No full-list
MRR is claimed. Eight plausible pairs are uncertain and excluded from binary
metrics; no binary accuracy is reported. Ten designed negatives are not verified
real negatives. Unlabelled candidates are not assumed negative.
One explicitly synthetic no-match query (syn-q03): zero candidates returned,
empty-result count 1/1 at the ranker's default lexical cutoff. This is not a
calibrated no-match decision. Two wording/similar-item queries remain qualitative
Day 1 fixtures, not additional metric queries. No campus accuracy is established.

## Loading real data later

CSV templates in data/templates/day1 have headers only; intake.json has empty
reports and pairs arrays and schema_version=1. JSON objects must use the CSV
column names. These are intake contracts, not automatic ingestion endpoints.
Read CSV with csv.DictReader (UTF-8 BOM tolerant) or JSON with json.load; extract
reports/pairs arrays, validate, then export reports using the same CSV headers.
Require unique report_id/pair_id, lost/found report_type, nonempty description,
valid ISO8601 event_date with timezone, source and consent references. Pair IDs
must resolve to one lost and one found report. Accept match/non_match only with
reviewer_id, reviewed_at, verification_method and evidence_reference. Otherwise
retain uncertain; never convert plausible to negative. Reject duplicate or dangling
IDs. Keep private identifiers and contact data outside retrieval text.

Use load_text_reports_csv(path, columns={name:name for name in
['report_id','report_type','description','item_name','category_id','location_id','event_date']})
after validation; split returned reports by report_type, construct TfidfRanker
with found reports, and rank lost reports. Pair labels remain separate evaluation
data and never enter the vectorizer. Rebuild via replace_inventory on inventory
changes. Review physical-item groups before splitting real queries. Do not use
reported_at as event_date or free-text location as validated location_id.
No real data or verified pair labels have arrived in these templates.

Day 2 checks: ranker unit suite, repeat-run output SHA256 equality, empty JSON intake contract, git diff --check, and unchanged raw/agent/ranker tree.
