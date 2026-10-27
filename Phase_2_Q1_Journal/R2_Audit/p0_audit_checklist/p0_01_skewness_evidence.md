# P0.1 Evidence — A.1 Skewness Interpretation

**Status:** DONE — 2026-10-14  
**Files checked:**
- `data/results/phase2_stageA/Report_3_October/json/module_a1_hubness.json`
- `Phase_2_Q1_Journal/reports/stage_A/module_a1_hubness_report.md`

## Verified Numbers

From `module_a1_hubness.json`:

| Model | Hubness skewness |
|---|---:|
| SEARLE | 2.6589632690804472 |
| Pic2Word | 2.6593284720061425 |

The ratio is approximately 1.0001x, so the older claim that Pic2Word has clearly higher global skewness is not supported by this JSON.

## Correction Applied

The regenerated A.1 report no longer states that Pic2Word has clearly higher global hubness skewness. The current R2 neighbor-level pipeline reports its own query-centric k-occurrence summary separately and does not use it to rescue the old claim.
