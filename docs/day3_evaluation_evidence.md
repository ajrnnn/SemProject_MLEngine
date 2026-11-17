# Day 3 evaluation and API evidence (SYNTHETIC ONLY)

Base: upstream/main 0f63385. Android integration is pending: this checkout has
no tracked AndroidManifest.xml, Gradle project or Kotlin app sources. No Android
build, emulator or API connectivity is demonstrated. Use the API demo path;
no ownership approval or item release is implemented or authorized by this demo.

## Reproduce

Install repository requirements in a project Python environment. Then run:

    python scripts/evaluate_day2_synthetic.py
    python -m scripts.demo_day3
    python scripts/capture_day3_evidence.py
    python -m unittest tests.test_day3_integration tests.test_nlp_retrieval -q
    git diff --exit-code -- results/day2_synthetic_evaluation.json data/raw matching_system
    git diff --check

The capture uses FastAPI TestClient, exercising HTTP routing and validation
in-process, not a network/emulator connection. It checks health and both preview
requests return 200, malformed input returns 422, and the Day 2 source hashes,
query assignments, metrics, uncertain counts and no-match output remain identical
to the committed baseline. The JSON artifact records actual API responses.
For a live local walkthrough use python -m uvicorn matching_system.api:app
--host 127.0.0.1 --port 8000 and POST the recorded requests to /preview/matches.
The service is a synthetic preview without authentication or persistence.

## Frozen synthetic evaluation

46 reports: 14 lost queries and 32 found inventory records. 32 designed pair
labels: 14 match, 8 plausible (uncertain), 10 non_match. Zero independently
verified real-world labels. Uncertain pairs are excluded from binary metrics;
no binary accuracy is reported. The unchanged grouped split is development n=11,
test n=3. Recall@5 is 1.0 for both and all 14; MRR@5 is 0.651515 development,
0.611111 test and 0.642857 overall. One authored no-match query returns no
candidates (1/1 empty), not proof that a physical counterpart cannot exist.

SHA256 synthetic_campus_reports.csv:
bb5c321664838769a9a800cf69acc7e0c2047894a0bb36dd5f7d71439e2e4996
SHA256 labelled_campus_pairs.csv:
e025ff08ce02905e0a75fb8adbf570d8a8db0fadde2056be0787a1b9ae34dda9
The capture artifact also includes the demo CSV hash and per-query rankings.

## Three demo cases to review

- Correct authored suggestion: demo-lost-bottle -> demo-found-metal, rank 1.
  Blue metal bottle with scratched lid; category agrees and dates are compatible,
  but location differs. Staff should review the location difference. This is an
  authored same-item scenario, not a verified real-world match.
- Misleading candidate: the same bottle query -> demo-found-plastic, rank 3.
  Blue bottle and scratched-lid wording overlaps, but plastic conflicts with the
  metal category. Inspect the conflict; similarity does not establish identity.
- Empty result: violet telescope marked SYNTHETIC-X999 -> no candidates.
  No shared lexical evidence in the demo inventory. Do not conclude no ownership
  claim or physical match exists. Request more details or review inventory.

Candidate evidence and suggested staff actions are advisory. Missing fields,
location differences and conflicts remain visible; no automatic release follows.
No screenshots apply: this change captures JSON HTTP evidence, not a UI screen.
Remaining limitations: tiny designed fixtures, partial relevance judgments,
uncalibrated lexical cutoff, no real-report validation, no Android integration,
no production authentication/persistence and no ownership verification.
Checks passed: 10 integration/retrieval tests; frozen evaluation comparison; HTTP 200/422; authored candidate presence; empty result; ownership_approved false; protected-file diff empty.
