# CLAUDE.md — agentic-doc-extraction

MSc thesis (Technical University of Crete): **Multimodal Agentic Workflows for Information
Extraction from Unstructured Documents** — Greek administrative / public-procurement PDFs
(mainly from Diavgeia). This is a research project: every change must serve a research
objective and be defensible before the thesis committee.

## Core research principle
An extracted entity or value is NOT correct merely because it appears in the document.
Its **semantic role** (e.g. awarded contractor vs. payment beneficiary vs. invitee) must be
supported by evidence. Keep these distinct: **Validation ≠ Grounding ≠ Correctness**
(a checksum-valid AFM does not prove it belongs to the contractor).

## Current priority (since 2026-11-27)
**Real-world evaluation on human-annotated Greek documents.** The synthetic adaptive-evidence
benchmark (v1/v2/v2.2) is **frozen**; extend it only if a concrete real-data limitation requires it.
Do not propose new frameworks, agents, services or architecture changes unless they directly
serve evaluation or the thesis. See the "Current State" section at the top of `PROJECT_STATUS.md`.

## Architecture (actual code)
`src/multimodal_graph.py` — a **page-level** LangGraph (one page per run):
```
load_document → assess_and_route ─┬→ process_page [digital|tesseract|paddleocr] ─┐
                                  └→ (vlm) ───────────────────────────────────────┤
extract_information (Groq qwen/qwen3.8-27b → PageExtraction) ←───────────────────┘
→ verify_extraction (evidence + AFM checksum) → semantic_verification (LLM, ≤2 role checks)
→ correction_controller → retry (OCR + text LLM) | END
```
- Nodes: `src/nodes/`; logic: `src/evaluation/`; ingestion/routing: `src/ingestion/`;
  LLM client: `src/extraction/llm_client.py`; schemas: `src/schemas/`.
- Document-level modules (`document_aggregator`, `document_verifier`, `document_evidence_selector`,
  `adaptive_evidence_selector`) are offline library code, **not wired into the graph**.
- Fields: `document_type`, `issuing_authority`, `recipient`, `contractor`, `contractor_tax_id`.

## Data & evaluation
- Corpus: `data/discovery/` (57 Diavgeia PDFs) + `data/metadata/`.
- Verified dev annotations: `benchmark_v1/pilot_annotations/` (9 pages, 8 PDFs, split `dev`).
  Legacy `data/annotations/` + `data/raw/` are pending/legacy — not ground truth.
- Guidelines: `benchmark_v1/ANNOTATION_GUIDELINES.md`. Results: `evaluation_results/`.
- Rules: dev ≠ test; select held-out test documents **before** running systems; freeze the
  evaluation protocol/config before test runs; never tune prompts on test documents; never mix
  page-level and document-level metrics; report confidence intervals for small samples;
  never overwrite existing predictions or annotations — create versioned files.

## Commands
- Tests (offline, mocked LLM): `.venv/bin/python -m pytest -q`
- `.venv-ocr` (Python 3.12) only for PaddleOCR experiments.
- Benchmark scripts: `python -m benchmark_v1.scripts.<name> ...` from repo root.
- Live runs call the Groq API (rate limits apply); do not run them without asking.

## How to work with the user (Nikos)
- Reply in **Greek**; use English for identifiers, code, metrics and standard terminology.
- Explain *why* a change is made; guide step by step; keep explanations concise.
- Workflow: understand existing code → identify issue → smallest change → tests →
  targeted + full regression → review `git diff` → explain outcome and limitations.
- Never rewrite working modules or add abstraction for its own sake. Challenge
  assumptions and say when a task is not worth it for the thesis.

## Documentation
After each **verified** milestone update `PROJECT_STATUS.md`: what was implemented,
architecture changes, tests + actual results, methodology/outcomes, limitations, next milestone.
Never mark something completed before verification. Keep the "Current State" section current.

## Git & safety
- Check `git status` before changes. No commit/push without explicit approval.
- No `git reset --hard`, destructive cleanup, deleting unknown files, or editing unrelated modules.
- Never read or print `.env`, API keys or credentials. Don't change `.gitignore`/permissions
  without explaining why. Use only public (Diavgeia) or anonymized documents; treat names,
  phone numbers and other personal data in documents with care before committing derived files.
