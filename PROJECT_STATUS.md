
# MSc Thesis — Project Status

Last updated: 2026-10-13

## 1. Research Goal
Multimodal Agentic Workflows for Information Extraction from Unstructured Documents.

Focus: Greek public-sector, procurement and legal documents.

Objective: Evidence-grounded, reliable information extraction using document parsing, OCR, VLMs, LangGraph orchestration and deterministic validation.

## 2. Existing Architecture
- LangGraph agentic extraction with validation/correction loop.
- Pydantic extraction schemas and deterministic validators.
- Digital/scanned PDF routing.
- Tesseract OCR and initial vision integration.
- SQLite checkpointing and execution metrics.

Important: The original pipeline was developed as a prototype and still requires a thorough architecture/code review.

## 3. Dataset
- Source: Diavgeia OpenData API.
- Discovery corpus: 57 PDFs, 379 pages.
- Categories: 27 assignments, 10 tenders, 10 awards, 10 contracts.
- PDF metadata: ADA, document type, SHA-256, page count.
- Human-annotated pilot: 3 independent real documents.
- One synthetic scanned derivative, excluded from independent evaluation.

Files:
- data/discovery/
- data/metadata/
- data/annotations/
- scripts/collect_diavgeia.py

The discovery corpus is exploratory, not a representative benchmark.

## 4. Corpus Profiling
Implemented:
- scripts/profile_corpus.py
- evaluation_results/corpus_profile.csv
- evaluation_results/page_profile.csv

Results:
- 379 pages.
- Mean: 6.65 pages/document.
- Median: 2 pages/document.
- Maximum: 63 pages.
- 84 pages containing embedded images.
- 3 pages with fewer than 100 extracted characters.

The three low-text pages were visually checked and were naturally almost empty.

Image coverage was added to page-level profiling.

## 5. OCR Experiments

Real case:
- ADA: Ψ6ΓΧ7ΛΛ-19Χ
- Page: 4
- Significant visible text missing from PyMuPDF extraction.
- PyMuPDF: approximately 164 extracted characters.

Tesseract:
- Version: 5.3.4
- Languages: ell+eng
- Resolution: 300 DPI
- OCR output: 2,983 characters
- Whitespace-normalized CER: 1.95%

PP-OCRv5:
- PaddleOCR: 3.4.1
- PaddlePaddle: 3.3.1
- Models: PP-OCRv5_mobile_det + el_PP-OCRv5_mobile_rec
- CPU, oneDNN disabled, 2 threads
- Resolution: 150 DPI
- OCR output: 2,992 characters
- Inference: 29.95 seconds
- Whitespace-normalized CER: 0.33%

CER evaluation:
- One human-verified reference span.
- Reference length: 307 characters.
- Tesseract edit distance: 6.
- PaddleOCR edit distance: 1.

IMPORTANT:
These are preliminary results from one manually aligned span.
Different image resolutions were used.
No general model superiority has been established.
Critical-field accuracy remains untested.

## 6. Development Environment
GitHub Codespaces, approximately 8 GB RAM, CPU-only.

- .venv: Python 3.14, existing pipeline.
- .venv-ocr: Python 3.12, neural OCR experiments.
- Tesseract installed with ell/eng.
- PaddleOCR working with mobile detection model.

The larger PaddleOCR server detection model failed due to runtime/memory constraints.

## 7. Evaluation Infrastructure
Implemented:
- Pydantic human annotation schemas with evidence.
- Annotation validation.
- Raw and normalized exact match.
- Initial automated contractor-name evaluation.
- OCR CER using RapidFuzz.

Key distinction:
Validation != Grounding != Correctness.

Original pipeline's 100% validity was not 100% extraction accuracy.

## 8. Next Steps
1. Select a suitable multimodal VLM and inference provider.
2. Test VLM transcription on the same real Greek document.
3. Compare OCR/VLM quality, latency and cost.
4. Extend evaluation to more pages and critical fields.
5. Review existing LangGraph architecture and integrate modular ingestion strategies.
6. Expand the dataset and establish a rigorous benchmark protocol.

## 9. Research Principles
- Ground truth must be independently human verified.
- Preserve source evidence and provenance.
- Do not infer undocumented values as ground truth.
- Avoid synthetic-data leakage.
- Distinguish exploratory findings from final thesis results.
- Measure accuracy, reliability, latency and cost.
- Prefer incremental, testable implementations.

## 10. Instructions for Any Continuing AI Assistant
Act as Co-Supervisor, Senior AI Architect and technical mentor.

- Continue from the current project state.
- Review actual repository code before proposing major changes.
- Explain concepts step by step.
- Prefer modern, research-grounded methods.
- Avoid unnecessary complexity and token overhead.
- Keep responses natural, concise and cohesive.
- Update this file after meaningful milestones.
- Do not restart the project from scratch.


## Multimodal Pipeline v1 — Implementation Progress

- Created `src/schemas/document.py`.
- Introduced `DocumentRecord`, `DocumentPage`, `TextLayer`.
- Created `src/ingestion/pdf_loader.py`.
- Created `src/ingestion/ocr_backend.py`.
- Successfully loaded real Diavgeia PDF into page-level representation.
- Successfully attached Tesseract OCR output as a second text layer.

Test document: Ψ6ΓΧ7ΛΛ-19Χ, page 4.

Results:
- Digital text: 164 characters.
- Tesseract OCR: 2,983 characters.
- Tesseract processing time: 13.036 seconds.

Next:
1. Define common processing backend interface.
2. Integrate PaddleOCR through isolated Python environment.
3. Add VLM processing backend.
4. Introduce quality-aware routing.
5. Integrate processing strategies into LangGraph.

### Processing Backends — Milestone Completed

- Defined common `PageProcessor` protocol.
- Implemented `TesseractProcessor` (Python 3.14).
- Implemented `PaddleOCRProcessor` (isolated Python 3.12 worker).
- Added subprocess-based integration with timeout and temporary files.
- Both processors return the common `TextLayer` schema.

Integration test: Ψ6ΓΧ7ΛΛ-19Χ, page 4.

- Tesseract: 2,983 characters, 11.233 sec, 300 DPI.
- PaddleOCR: 2,992 characters, 36.437 sec, 150 DPI.

Both backends are operational. Latencies are preliminary and not directly comparable.

Next milestone: VLM backend and evidence-aware multimodal extraction.


## Multimodal Extraction Pilot — 2026-10-18

Document: Ψ6ΓΧ7ΛΛ-19Χ, page 1.
Task: Extract document type, issuing authority, recipient, contractor and contractor tax ID.

Pipeline A: PaddleOCR (150 DPI) → Qwen3.8-27B
- OCR: 2,799 characters, 38.851 sec.
- LLM: 1.01 sec.
- Five fields semantically consistent with page-level reference.

Pipeline B: Image (150 DPI) → Qwen3.8-27B
- VLM latency: 1.32 sec.
- Five fields semantically consistent with page-level reference.
- Structured output initially failed; succeeded after explicit schema instructions.

Findings:
- Both pipelines distinguished recipient from contractor.
- OCR reading order was imperfect.
- Evidence fidelity requires independent verification.
- Full-page VLM transcription was incomplete in an earlier experiment.

Limitations:
- Single page, exploratory comparison.
- No automated field-level evaluation yet.
- No repeated end-to-end latency measurements.
- Different compute backends; timings not directly comparable.

Next:
1. Implement deterministic evidence verification.
2. Build reproducible field-level evaluator.
3. Integrate processing and extraction into LangGraph.
4. Expand evaluation across multiple document types.

Value grounding succeeded for all three present fields, while recipient evidence matching failed due to OCR reading-order distortion. Visual inspection confirmed the recipient relationship, motivating spatially grounded verification.


### Layout-Aware Verification — Milestone

- Implemented initial spatial relation checker.
- Tested on real PaddleOCR bounding boxes.
- Document: Ψ6ΓΧ7ΛΛ-19Χ, page 1.
- Label: ΠΡΟΣ:
- Value: ΓΕΩΡΓΙΟΣ Μ. ΤΣΑΚΟΥΜΗΣ ΚΑΙ ΣΙΑ Ε.Ε.
- Horizontal gap: 14 px.
- Vertical gap: 2 px.
- Spatial relation: nearby, right-of.
- Visual inspection supports recipient interpretation.
- Spatial proximity alone is not proof of semantic role.

Next: Preserve OCR spatial elements in document schema and integrate processing/extraction/verification into LangGraph.