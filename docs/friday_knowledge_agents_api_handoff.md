# Friday handoff: knowledge agents and preview API

This handoff describes the implementation on the current branch. The preview
uses the synthetic inventory at `data/fixtures/day3/demo_reports.csv`; it does
not persist reports, verify ownership, or authorize an item release.

## Running components and boundaries

`matching_system.api` validates requests and loads the fixed synthetic inventory
once at process startup. `MatchingPipeline` asks `TfidfRanker` for up to five
lexical candidates, passes each candidate's `text_similarity` to
`assess_candidate`, and passes the resulting facts to
`recommend_staff_workflow`. The matching agent does not retrieve or score
reports. The workflow agent does not approve ownership or release. TF-IDF
similarity is a cosine score, not a match probability or an ownership estimate.

## Matching facts and inference

`assess_candidate(lost, found, text_similarity)` requires a lost report first,
a found report second, and a finite similarity score from 0 through 1.
Invalid arguments raise `ValueError`; the API does not expose these internal
errors as validation detail.

It emits these facts, in order:

| `fact_id` | Compared input | Meaning |
| --- | --- | --- |
| `category_id` | Lost and found category | Trimmed, case-insensitive equality is agreement. Missing either side is unknown. A broad value (`accessories`, `general`, `misc`, `miscellaneous`, `other`) on either side is ambiguous, not agreement or a decisive conflict. Other unequal values conflict. |
| `location_id` | Lost and found location | Trimmed exact equality is agreement; unequal known values conflict; missing either side is unknown. A location conflict is non-dispositive and never removes a candidate. |
| `event_date` | Lost and found ISO date | Missing or unparsable dates are unknown. A found date on/after the lost date is compatible/agreement; a found date before the lost date is a conflict. |
| `text_similarity` | Retrieval score | Recorded as lexical evidence only; it is not compared against a match threshold. |

Fact statuses are `agreement`, `conflict`, `ambiguous`, and `unknown`.
Aggregate `evidence_state` uses precedence: any conflict, then any ambiguity,
then any agreement, otherwise unknown. This summary does not decide the
candidate. `candidate_recommendation` is always `staff_review`.

### Matching rule and reason catalog

Every inference emits a `rule_trace` entry linking its rule ID, fact ID, reason
code, and status. `rule_ids` and `reason_codes` remain available as parallel
summary lists in the same trace order.

| Rule ID | Fact | Reason code | Trigger |
| --- | --- | --- | --- |
| `MA-R001` | `category_id` | `CATEGORY_AGREEMENT` | Both categories known, narrow, and equal ignoring case/outer whitespace. |
| `MA-R002` | `category_id` | `CATEGORY_CONFLICT` | Both categories known and unequal; candidate still remains reviewable. |
| `MA-R003` | `category_id` | `CATEGORY_UNKNOWN` | Either category is missing/blank. |
| `MA-R004` | `location_id` | `LOCATION_AGREEMENT` | Both locations known and equal after trimming. |
| `MA-R005` | `location_id` | `LOCATION_DIFFERENCE_NON_DISPOSITIVE` | Both locations known and unequal after trimming. |
| `MA-R006` | `location_id` | `LOCATION_UNKNOWN` | Either location is missing/blank. |
| `MA-R007` | `event_date` | `EVENT_DATE_COMPATIBLE` | Both dates parse and found date is on/after lost date. |
| `MA-R008` | `event_date` | `EVENT_DATE_DIFFERENCE_NON_DISPOSITIVE` | Both dates parse and found date is earlier than lost date. |
| `MA-R009` | `event_date` | `EVENT_DATE_UNKNOWN` | Either date is missing or fails parsing. |
| `MA-R010` | `text_similarity` | `TEXT_SIMILARITY_RECORDED` | Always emitted to mark the supplied retrieval score as lexical evidence. |
| `MA-R011` | `category_id` | `CATEGORY_AMBIGUOUS` | Either known category is one of the broad values listed above. |

The matching trace records the corresponding status (`agreement`, `conflict`,
`ambiguous`, `unknown`, or `recorded`). Category, location, and date facts
include their structured values in the internal assessment object; the
plain-language explanation does not repeat those values.

## Staff workflow and constraints

`recommend_staff_workflow(assessment)` selects exactly one next action, using
this precedence:

| Rule ID | Reason code | Action | Condition |
| --- | --- | --- | --- |
| `WF-R002` | `CONFLICTS_REQUIRE_REVIEW` | `review_conflicts` | Aggregate evidence contains a conflict. |
| `WF-R003` | `AMBIGUOUS_CATEGORY_REQUIRES_REVIEW` | `request_details` | No conflict takes precedence and a fact is ambiguous. |
| `WF-R003` | `MISSING_DETAILS_REQUIRE_REVIEW` | `request_details` | No conflict/ambiguity takes precedence and a fact is unknown. |
| `WF-R001` | `STAFF_REVIEW_REQUIRED` | `staff_review` | Facts contain no conflict, ambiguity, or unknown. |
| `WF-R004` | `OWNERSHIP_NOT_AUTOMATED` | — | Always emitted; `ownership_approved` is always `false`. |
| `WF-R005` | `RELEASE_NOT_AUTOMATED` | — | Always emitted; `release_authorized` is always `false`. |

The workflow trace contains the selected action rule/reason/fact followed by
the ownership and release constraints. A review action is a recommendation to
staff, not an ownership decision. No code path in this workflow returns true
for either approval or release authorization.

## Plain-language candidate explanation

The pipeline attaches an `explanation` to each match. It names only the fixed
fact labels `category`, `location`, and `event date`, then describes their
statuses as agrees, differs, broad/ambiguous, or missing/unknown. It describes
the workflow action and always clarifies that similarity is lexical evidence,
ownership is unverified, and release is not authorized. The explanation is
constructed from these labels/statuses and the workflow enum, not from report
names, descriptions, IDs, contacts, or submitted values.

## HTTP API contract

### `GET /health`

Returns HTTP 200:

```json
{
  "status": "ok",
  "mode": "synthetic_preview",
  "persistence": false
}
```

This identifies the local synthetic preview; it is not a production-readiness
or data-safety assertion.

### `POST /preview/matches`

The request is a JSON object with unknown fields forbidden:

| Field | Type | Requirement/default |
| --- | --- | --- |
| `item_name` | string | Required; trimmed; 1–160 characters. |
| `description` | string | Required; trimmed; 1–4000 characters. |
| `category_id` | string or null | Optional; defaults to null. |
| `location_id` | string or null | Optional; defaults to null. |
| `event_date` | string or null | Optional; defaults to null; must be `YYYY-MM-DD` and a valid calendar date. |
| `limit` | integer | Optional; defaults to 5; range 1–5. |

The API rejects recognizable email addresses, phone-like digit sequences, and
values following common private-ID labels (student ID, national ID, ID number,
passport number/no.) in the free-text fields `item_name`, `description`,
`category_id`, and `location_id`. Recognized ISO dates are excluded from the
phone-like sequence check. A rejected request returns HTTP 422 with only:

```json
{"detail": "Invalid general-item preview request"}
```

The same generic response is used for other request validation failures
(missing/extra fields, lengths, types, bad dates, and invalid limits). The
handler does not return Pydantic's rejected values or field input.

This is a focused obvious-pattern safeguard, not a general PII detector or a
claim that arbitrary real reports are safe to submit. It can miss unusual
formats, unlabeled identifiers, names, addresses, indirect identifiers, and
other sensitive content; it can also reject benign text that resembles a
phone/ID. Do not send unreviewed real reports to this synthetic preview.
Permitted real intake still requires authorized access, human privacy review,
removal/minimization of personal data from item names and descriptions,
restricted handling of any necessary claimant identifiers, and validation of
source/provenance before indexing.

For a valid request, HTTP 200 response top-level fields are:

| Field | Meaning |
| --- | --- |
| `mode` | Always `synthetic_preview`. |
| `status` | `possible_matches` if at least one lexical candidate is returned; otherwise `no_lexical_candidates`. |
| `score_meaning` | Fixed text explaining TF-IDF cosine similarity is not match or ownership probability. |
| `matches` | Up to `limit` candidate objects, possibly empty. |

Each match combines the matching assessment with:

- `lost_report_id`, `found_report_id`, `text_similarity`,
  `evidence_state`, `candidate_recommendation`;
- `facts`, `rule_ids`, `reason_codes`, and `rule_trace`;
- `explanation`, the plain-language staff explanation;
- `workflow`: its report IDs, `action`, `ownership_approved: false`,
  `release_authorized: false`, rule/reason lists, and workflow trace.

When retrieval finds no positive lexical overlap (or inventory is empty), the
response has `status: "no_lexical_candidates"` and `matches: []`. This is not a
finding that no physical counterpart exists; staff should obtain more detail
or search manually. The API loads the bundled fixture at startup and does not
persist or hot-reload requests/inventory.

### Sample response excerpt

With the README metal-bottle query, the first synthetic fixture candidate
currently returns this excerpt:

```json
{
  "status": "possible_matches",
  "matches": [{
    "found_report_id": "demo-found-metal",
    "text_similarity": 0.835001,
    "evidence_state": "conflict",
    "candidate_recommendation": "staff_review",
    "explanation": "Facts: category agrees; location differs; event date agrees. Staff should review the conflicting details. Text similarity is lexical evidence, not a probability. Ownership is unverified; release is not authorized.",
    "rule_ids": ["MA-R001", "MA-R005", "MA-R007", "MA-R010"],
    "reason_codes": ["CATEGORY_AGREEMENT", "LOCATION_DIFFERENCE_NON_DISPOSITIVE", "EVENT_DATE_COMPATIBLE", "TEXT_SIMILARITY_RECORDED"],
    "workflow": {
      "action": "review_conflicts",
      "ownership_approved": false,
      "release_authorized": false,
      "rule_ids": ["WF-R002", "WF-R004", "WF-R005"],
      "reason_codes": ["CONFLICTS_REQUIRE_REVIEW", "OWNERSHIP_NOT_AUTOMATED", "RELEASE_NOT_AUTOMATED"]
    }
  }]
}
```

This score is from the current fixture run; exact cosine values depend on the
fixture index and implementation version. Consult the response's
`facts` and `rule_trace` for structured evidence. See [Day 4 NLP handoff](./day4_nlp_handoff.md)
for corpus and retrieval limits.

## Verification

Run the API and all repository tests from the project root:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

The focused HTTP tests cover valid previews, empty lexical results, agreement,
conflict, missing details, and obvious-contact/private-ID rejection with
response non-disclosure.
