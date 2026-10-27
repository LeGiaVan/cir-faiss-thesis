# P0.4 Evidence — A.1 HNSW In-degree vs FlatIP N10

**Status:** DONE — 2026-10-14  
**Files checked:**
- `Phase_2_Q1_Journal/R2_Audit/module_a1_revision/results/step1_hnsw_indegree.json`
- `Phase_2_Q1_Journal/reports/stage_A/module_a1_hubness_report.md`

## Verified Numbers

From `step1_hnsw_indegree.json`:

| Model | Gallery size | In-degree=0 ratio | Retention@10 |
|---|---:|---:|---:|
| SEARLE | 123403 | 0.00000810353070832962 | 0.9698039215686275 |
| Pic2Word | 123403 | 0.0001620706141665924 | 0.9058823529411765 |

The R2 script directly measures HNSW layer-0 in-degree instead of inferring graph degree from FlatIP `N10`.

## Correction Applied

The regenerated A.1 report distinguishes exact top-10 k-occurrence from HNSW graph in-degree. It no longer states that FlatIP Anti-hubs have no HNSW incoming edges.
