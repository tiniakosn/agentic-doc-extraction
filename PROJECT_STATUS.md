# MSc Thesis — Project Status

**Title:** Multimodal Agentic Workflows for Information Extraction from Unstructured Documents
**University:** Technical University of Crete — MSc Intelligent Systems
**Supervisor:** N. Papadakis | **Committee:** Tsafarakis, Daras
**Last updated:** 2026-11-28

> One-page snapshot. Full history: `docs/research_log.md`. Weekly supervisor updates: `docs/weekly_updates.md`.
> Update this file after every milestone.

## 1. System (active implementation)

`src/multimodal_graph.py` (LangGraph, page-level):

    load → assess_and_route → [process_page] → extract → verify → semantic_verify → correction_controller → (retry | end)

- Routing: digital text / Tesseract OCR by page-quality rules (VLM only if requested explicitly).
- Extraction: 5 fields (document_type, issuing_authority, recipient, contractor, contractor_tax_id),
  each with value / status / evidence. Model: `qwen/qwen3.8-27b` via Groq (free tier), temperature 0.
- Verification: value & evidence grounding, AFM checksum, spatial check (ΠΡΟΣ:),
  absence check for not_present fields, LLM role verification (max 2 per page).
- Correction: 1 bounded retry with alternative processing method.
- Token usage and latency logged per LLM call.

## 2. Data

- Corpus: 57 Diavgeia PDFs, 379 pages (`data/discovery`, `data/metadata`).
  Routing v1 distribution: 358 digital / 12 OCR / 9 review (decision distribution, not accuracy).
- Verified dev annotations: 9 pages / 8 PDFs (`benchmark_v1/pilot_annotations`).
- Held-out test set: **not yet created**.

## 3. Development results (dev only — not held-out accuracy)

| Strategy | Field agreement (n=45) |
|---|---|
| Digital + LLM | 30/45 (66.7%) |
| Direct VLM | 24/45 (53.3%) |
| Adaptive workflow | 32/45 (71.1%) |

Verification after absence check: review 20 → 6, pages completed 0/9 → 3/9,
false acceptance 7/25 (strict), 0 introduced by the absence check.
Index of result files: `evaluation_results/benchmark_v1/README.md`.

## 4. Key findings so far

1. Validation ≠ grounding ≠ correctness.
2. Direct VLM assigned a mobile number as contractor AFM and fabricated matching evidence;
   AFM checksum + OCR retry corrected it.
3. Corrupted digital text layers (unassigned Unicode) are detectable and routed to OCR.
4. OCR reading order can merge header columns, producing wrong authority/recipient that still passes grounding.
5. Grounding against a noisy OCR source confirms OCR errors (e.g. misread surname accepted).
6. Payment beneficiary vs. awarded contractor remains a role-confusion case even with LLM role verification.

## 5. Timeline (target: core work complete by end of December 2026)

| Week | Dates | Goal | Status |
|---|---|---|---|
| W48 | 23–29 Nov | Cleanup, token logging, absence check, project status | ✅ |
| W49 | 30 Nov–6 Dec | Reflection, VLM fallback, multi-page runner; freeze evaluation protocol | ⬜ |
| W50 | 7–13 Dec | Collect & annotate held-out test set (~50 pages); metrics module | ⬜ |
| W51 | 14–20 Dec | Main experiments + noise experiment (daily runs within free quota) | ⬜ |
| W52 | 21–27 Dec | Error analysis; write Architecture & Methodology chapters | ⬜ |
| W53 | 28 Dec–3 Jan | Results chapter draft → send to supervisor | ⬜ |
| Jan | — | Introduction, related work, polish, presentation | ⬜ |

## 6. Roadmap

- [x] Cleanup: legacy prototype, superseded synthetic v1/v2, single normalization module
- [x] Token usage logging
- [x] Absence check + text-anchor support in final decisions
- [ ] Reflection: error feedback to the LLM on retry
- [ ] VLM in adaptive routing / fallback
- [ ] Multi-page runner (per-page graph + document aggregation)
- [ ] Held-out test set (~50 pages, stratified, annotated before any run)
- [ ] Metrics: per-field P/R/F1, CIs, hallucination & false-acceptance rates, strict + lenient
- [ ] Noise experiment (synthetic degradations of digital pages)
- [ ] Thesis text

## 7. Constraints

- Free tools only. Groq free tier ≈ 200K tokens/day; ~5K tokens/page → ~35–40 pages/day.
- GitHub Codespaces, CPU only, ~8 GB RAM.
- Do not tune on the test set. Freeze configuration before the held-out run.