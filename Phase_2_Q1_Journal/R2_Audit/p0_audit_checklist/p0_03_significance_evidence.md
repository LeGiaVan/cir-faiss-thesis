# P0.3 Evidence — A.1 Statistical Significance

**Status:** DONE — 2026-10-14  
**Files checked:**
- `data/results/phase2_stageA/Report_3_October/json/module_a1_hubness.json`
- `Phase_2_Q1_Journal/R2_Audit/module_a1_revision/results/step2_bootstrap_ci.json`
- `Phase_2_Q1_Journal/reports/stage_A/module_a1_hubness_report.md`

## Verified Numbers

From the original A.1 JSON:

| Model | p-value | Significant at 0.05 |
|---|---:|---|
| SEARLE | 0.2022517444988281 | false |
| Pic2Word | 0.5442628824232023 | false |

From the R2 neighbor-level bootstrap JSON:

| Model | Anti-hub `N10=0` observations |
|---|---:|
| SEARLE | 0 |
| Pic2Word | 0 |

The neighbor-level exact top-10 table has no `N10=0` rows by definition: an item that appears in an exact top-10 list has `N10 >= 1`.

## Correction Applied

The regenerated A.1 report uses `CHƯA KẾT LUẬN` and does not claim `p < 0.05`. It explicitly notes that the neighbor-level Anti-hub group is not testable in the exact top-10 table.
