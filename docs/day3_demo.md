# Day 3 local demo and error review

Run `python -m scripts.demo_day3` from the repository root. For the HTTP walkthrough, run `python -m uvicorn matching_system.api:app --host 127.0.0.1 --port 8000` and use `POST /preview/matches` in `/docs` with the README example. All demo reports in `data/fixtures/day3/demo_reports.csv` are invented engineering fixtures.

Observed on the fixed fixture inventory:

| Query/candidate | Text rank | Agent evidence | Staff action |
| --- | ---: | --- | --- |
| Blue scratched metal bottle / `demo-found-metal` | 1 | Category agrees; found location differs; dates are compatible. | Review the location difference. |
| Same query / `demo-found-unknown` | 2 | Category and date are missing; location agrees. | Request details. |
| Same query / `demo-found-plastic` | 3 | Similar words, but metal/plastic categories conflict. | Inspect the conflict; do not infer ownership. |
| Violet telescope with no counterpart | No candidate | No shared lexical evidence in this fixture inventory. | No automated no-match conclusion. |

The plastic bottle is a deliberately misleading lexical candidate. The first-ranked metal bottle is an authored same-item scenario, not independently verified evidence. This demo proves that the ranker, matching agent, workflow agent and HTTP route can run together; it does **not** measure campus accuracy. Text scores are cosine similarities, not match probabilities. The API does not persist reports, authenticate staff, handle private IDs or connect to the Android app.
