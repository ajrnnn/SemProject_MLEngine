# Day 1 data audit

46 synthetic reports: 14 lost, 32 found. 32 designed pairs: 14 match,
8 plausible, 10 non_match. Ledger contains 46 report rows and 32 pair rows; three
additional synthetic queries cover wording variation, similar items and no match.
Raw files remain unchanged. No real-campus accuracy is claimed.

Plausible is uncertain, excluded from binary metrics. All labels are synthetic
design assertions awaiting independent review, including non_match. Proposed
physical groups are provisional: join the report groups identified by each
match pair before grouped holdout; unresolved pairs must be adjudicated.
Missing evidence: real reports, consent, collection provenance, independent
review, verified ownership/identity, verified negatives and representative coverage.

## Real intake

CSV templates are headers only; JSON arrays are empty. Use CSV field names
as keys of objects in reports and pairs. Require unique IDs, report_type
lost/found, nonempty description, ISO 8601 dates with offset and source reference.
Pair references must resolve to a lost and a found report. Labels are match,
non_match or uncertain. Verified labels require reviewer, review timestamp,
verification method and evidence reference; pending records stay uncertain.
Keep private IDs and contact details out of model text; use protected evidence
references. Obtain consent before using real reports. Never fabricate evidence.

Legacy loader mapping: report_id, report_type and description map directly;
item_name maps to category as temporary legacy fallback only. Free-text location
is not a validated location_id; reported_at is not verified event_date.
Fit only on found inventory and rebuild on changes, per nlp_day1_handoff.md.
Evaluate ranking separately; use reviewed physical-item groups for holdout.
Synthetic fixtures cannot establish real-campus matching accuracy.

Initial audit checks: ledger coverage 78 rows; uncertain mapping 8; 46 unique report IDs; pair references resolve; three query rows; JSON parses. These checks validate structure, not the truth of the designed labels.
