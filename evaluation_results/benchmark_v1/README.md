# Benchmark v1 — Development results (9 verified pages, 8 PDFs)

All results here are DEVELOPMENT results, not held-out test accuracy.

## Official development results (cited in the thesis)
| File | Content |
|---|---|
| `evaluation_verified_dev_v1.*` | Baselines (Digital+LLM, Direct VLM) vs verified annotations |
| `strategy_comparison_dev_v1.json` | 3-strategy comparison: 30/45, 24/45, 32/45 |
| `evaluation_workflow_dev_v1.*` | Adaptive workflow, before absence check (20 review) |
| `evaluation_workflow_dev_v2.json` | Adaptive workflow, after absence check (6 review, 3/9 pages completed) |

## Raw runs (inputs to the evaluations above)
| File | Content |
|---|---|
| `pilot_resumed_20261112T173616Z.json` | Baseline predictions (complete) |
| `workflow_pilot_20261122T153546Z.json` | Workflow run, before absence check |
| `workflow_pilot_20261128T091330Z.json` | Workflow run, after absence check |

## Superseded or diagnostic (kept for reproducibility; do not cite as results)
| File | Reason |
|---|---|
| `pilot_20261112T172532Z.json`, `pilot_20261112T173144Z.json` | Partial runs before rate-limit resume |
| `evaluation_exploratory_v1/v2.*` | Computed on provisional (unverified) annotations |
| `evaluation_adaptive_workflow_dev_v1.json` | Earlier variant of workflow evaluation |
| `disagreement_report_v1.json` | Exploratory disagreement listing |
| `role_verification_*.json` | Role verifier on 3 hand-picked claims (prompt tuned on them) |
| `corinth_document_verification_v1.json` | Multi-page verification diagnostic (1 document) |
| `text_layer_comparison/` | Digital vs Tesseract text for the corrupted-text case (KENAP) |