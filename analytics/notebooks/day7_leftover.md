# Day 7 — LEFTOVER / BLOCKED ITEMS

The following Day 7 deliverables cannot currently be completed because the required real candidate-ranking output and verified ground truth are unavailable.

## 1. Real Candidate Score-Breakdown Visualization — LEFTOVER

Status: BLOCKED

Reason:
`vessel_candidates` currently contains 0 rows.

Therefore the following real candidate values are unavailable:
- MMSI
- rank
- total_score
- feature_scores
- weighted_contributions
- uncertainty_score
- evidence_json

No synthetic/demo candidate values will be generated.

Required to complete:
- Actual persisted candidate-ranking output
- Candidate-wise numerical feature scores
- Weighted contributions
- Final total scores
- Rank

---

## 2. Candidate Reduction — LEFTOVER

Status: BLOCKED

Reason:
No real end-to-end compatible candidate-ranking run has produced persisted candidates.

Required:
- Candidate count before filtering
- Candidate count after compatibility/spatial/temporal filtering
- Final ranked candidate count

---

## 3. Ranking Stability — LEFTOVER

Status: BLOCKED

Reason:
No actual ranked candidate set is currently available for comparison across runs.

Required:
- At least two comparable real/test-fixture ranking outputs
- Candidate ranks and scores for each run

---

## 4. Recall@1 / Recall@3 — NOT COMPUTED

Status: BLOCKED

Reason:
No independently verified ground-truth vessel/MMSI is available.

Therefore:
- Recall@1: NOT COMPUTED
- Recall@3: NOT COMPUTED

No candidate will be treated as ground truth merely because it is ranked first.

---

## 5. Numerical Evidence Statement Audit — LEFTOVER

Status: BLOCKED

Reason:
Actual persisted candidate feature values are unavailable.

Required:
- Candidate-wise numerical feature values
- Final scores
- Weighted contributions
- Evidence JSON/statements

The evidence statement must remain:

"Highest-ranked candidate under available evidence.
This is an investigative lead, not a confirmed polluter."

---

## 6. End-to-End TEST_FIXTURE Candidate Ranking — LEFTOVER

Status: BLOCKED / DEPENDENCY

The prototype-aligned timeline is available, but the current scenario has not yet produced a persisted candidate-ranking result.

Potential inputs identified:
- Scenario: `SPILL_TEST3_001`
- Observation/SAR timestamp: `2025-01-08T18:49:10Z`
- Origin window: `2025-01-08T06:49:10Z` to `2025-01-08T18:49:10Z`
- Drift corridor: `ml/day5_outputs/origin_corridor.geojson`
- Drift mode: `analyst-parameter-driven`
- Data mode: `TEST_FIXTURE`

Important provenance limitation:
The aligned SAR timestamp is not independently verified SAR metadata. Therefore this scenario must not be represented as a REAL SAR/AIS attribution event.

Required before this can be completed:
- Compatibility logic explicitly permitting TEST_FIXTURE ranking
- Actual AIS track-level feature computation
- Existing scoring engine execution
- Actual ranking output
- Persistence/retrieval evidence

No compatibility gate will be bypassed to force candidate generation.
No synthetic MMSI, score, AIS position, or ground-truth value will be introduced.

---

## Day 7 Leftover Summary

| Item | Status |
|---|---|
| Real candidate score-breakdown | LEFTOVER |
| Candidate reduction | LEFTOVER |
| Ranking stability | LEFTOVER |
| Recall@1 | NOT COMPUTED |
| Recall@3 | NOT COMPUTED |
| Evidence statement audit | LEFTOVER |
| TEST_FIXTURE end-to-end ranking | LEFTOVER / DEPENDENCY |

These items should be revisited when actual compatible candidate-ranking output and/or verified ground truth become available.