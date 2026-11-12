
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

### LangGraph Integration — October 2026

Implemented:
- WorkflowState
- load_document_node
- process_page_node
- extract_information_node
- verify_extraction_node
- Reusable LLM extractor

Validated:
- Load → Process → Extract end-to-end with Tesseract + Qwen.
- PaddleOCR integration with 69 spatial text regions.
- Verification node independently tested with saved OCR/LLM results.

Evidence verification pilot:
- document_type: needs_review (0.959)
- issuing_authority: supported (1.0)
- recipient: unsupported (0.702)
- contractor: not_applicable
- contractor_tax_id: not_applicable

Important:
- Evidence matching is not equivalent to factual correctness.
- OCR reading-order distortion affects textual grounding.
- Spatial evidence may help verify entity roles.
- Full four-node graph execution remains to be tested.

Next:
1. Test full four-node LangGraph workflow.
2. Integrate value and spatial grounding.
3. Add explicit verification outcomes.
4. Design adaptive routing and targeted correction.
## Research Checkpoint — 2026-10-18

### LangGraph v1
- Implemented and tested Load → Process → Extract → Verify.
- Real end-to-end run completed with Tesseract + Qwen.
- Document: Ψ6ΓΧ7ΛΛ-19Χ, page 1.
- Total execution time: 13.371 seconds.
- Output: evaluation_results/langgraph_v1_page1.json.

### Verification Layer v2
- Integrated textual value grounding.
- Integrated evidence matching.
- Integrated OCR region matching and spatial relation checks.
- Tested with saved PaddleOCR and LLM outputs.

Results:
- document_type: value supported; evidence needs_review (0.959).
- issuing_authority: value and evidence supported.
- recipient: value supported; evidence unsupported (0.702).
- recipient value region: 30.
- recipient label region: 32.
- horizontal gap: 14 px; vertical gap: 2 px.
- contractor and contractor_tax_id: absence not independently verified.

### Important Research Finding
LLM-generated evidence is not necessarily an exact source quotation.

In the recipient case:
- OCR reading order placed the company before the label ΠΡΟΣ.
- The LLM reconstructed the logical relationship.
- The evidence string differed from the OCR text.
- Spatial OCR regions supported the label-value association.

Value grounding, evidence fidelity and semantic role
verification must be evaluated separately.

### Current Limitations
- Verification is still heuristic and experimental.
- Spatial proximity alone does not prove entity roles.
- No general multi-region evidence linking yet.
- No reliable absence verification.
- Adaptive routing and targeted correction are not implemented.
- Evaluation dataset is still too small for general conclusions.

### Next Steps
1. Stabilize Verification v2 and its output semantics.
2. Integrate source-anchored region references into verification.
3. Implement quality assessment and adaptive routing.
4. Implement bounded, targeted correction.
5. Expand human annotations and benchmark evaluation.
6. Compare accuracy, grounding, latency and cost.

### Handoff Note
The original Gemini prototype remains in the repository.
The new multimodal architecture is being developed separately.
Reuse existing components rather than duplicating business logic.
Explain architectural decisions and theory during implementation.
Keep PROJECT_STATUS.md updated after significant milestones.

---

# PROJECT HANDOFF CHECKPOINT — 2026-10-20

## 1. Thesis Context

Title: Multimodal Agentic Workflows for Information Extraction
from Unstructured Documents.

University: Technical University of Crete.
Domain: Greek public procurement and administrative documents.
Primary source: Diavgeia.

Research objective:
Develop and evaluate an adaptive, evidence-grounded,
multimodal document information extraction workflow.

Core framework: LangGraph.
Development environment: GitHub Codespaces.

## 2. Current Architecture

New architecture:
PDF -> Load -> Process -> Extract -> Verify

Implemented components:

- src/multimodal_graph.py
- src/schemas/workflow_state.py
- src/schemas/document.py
- src/schemas/page_extraction.py
- src/schemas/evidence.py
- src/nodes/load_document.py
- src/nodes/process_page.py
- src/nodes/extract_information.py
- src/nodes/verify_extraction.py
- src/ingestion/pdf_loader.py
- src/ingestion/ocr_backend.py
- src/ingestion/paddle_backend.py
- src/ingestion/page_quality.py
- src/ingestion/routing.py
- src/extraction/llm_extractor.py
- src/evaluation/evidence_verifier.py
- src/evaluation/spatial_verifier.py
- src/evaluation/region_grounding.py
- src/evaluation/source_anchor.py

The original Gemini prototype remains in src/graph.py.
Prefer the newer architecture for continued development.

## 3. Processing Backends

Digital: PyMuPDF.
OCR: Tesseract (Greek + English).
OCR: PaddleOCR PP-OCRv5 Greek recognition.
LLM: Qwen via Groq API.

Two Python environments:
- .venv: main application.
- .venv-ocr: PaddleOCR dependencies.

PaddleOCR uses a separate subprocess worker.

## 4. Completed Integration

Real end-to-end LangGraph execution succeeded:

Load -> Tesseract -> Qwen -> Verification.

Document: Ψ6ΓΧ7ΛΛ-19Χ.
Page: 1.
Execution time: 13.371 seconds.

Output:
evaluation_results/langgraph_v1_page1.json

Note:
Verification status "verified" currently means verification
executed, NOT that all fields are factually correct.

## 5. Source-Anchored Evidence v1

Implemented and independently tested:
- Value grounding
- Evidence string matching
- OCR region matching
- Spatial relation checks
- SourceReference generation

Real example:
Document: Ψ6ΓΧ7ΛΛ-19Χ, page 1.
Recipient: ΓΕΩΡΓΙΟΣ Μ. ΤΣΑΚΟΥΜΗΣ ΚΑΙ ΣΙΑ Ε.Ε.
Value region: 30.
Label ΠΡΟΣ region: 32.
Horizontal gap: 14 pixels.
Vertical gap: 2 pixels.

Value grounding: supported (1.0).
LLM evidence matching: unsupported (0.702).
Spatial relation: nearby and right-of.

Source anchoring integration test: PASS.

Important:
Source references establish provenance of matched text,
not automatically factual correctness or semantic role.

The full production graph with source anchoring has not
yet been rerun end-to-end.

## 6. Corpus

Initial corpus:
57 PDFs, 379 pages.

Important artifacts:
- evaluation_results/corpus_profile.csv
- evaluation_results/page_profile.csv
- evaluation_results/routing_analysis.csv
- evaluation_results/routing_audit.pdf
- evaluation_results/routing_audit_labels.csv

The routing audit contains 15 sampled pages.

Labels are provisional visual assessments, NOT
independently validated ground truth.

## 7. Adaptive Routing v1

Initial rule-based routing:
- digital
- tesseract
- review

Corpus distribution:
- Digital: 358 / 379
- Tesseract: 12 / 379
- Review: 9 / 379

This is decision distribution, NOT accuracy.

## 8. Adaptive Routing v2

Implemented experimental function:
choose_processing_route_v2()

Location:
src/ingestion/routing.py

Page quality features:
- text_chars
- image_count
- image_coverage
- suspicious_text_ratio
- visual_ink_ratio
- greek_letter_ratio

Visual ink uses grayscale rendering at 72 DPI,
with pixel threshold 220.

Experimental routing thresholds are not calibrated.

Audit comparison:
- 15 development pages
- 6 decisions changed from v1 to v2
- 4 Tesseract -> Review
- 2 Review -> Tesseract
- 9 decisions unchanged

Known document Ψ6ΓΧ7ΛΛ-19Χ:
Page 1: v1 Review -> v2 Tesseract.
Page 4: Tesseract in both versions.

Results suggest improvements on the development sample,
but do NOT establish generalization.

## 9. Important Methodological Decisions

- Validation != grounding != factual verification != evaluation.
- Ground truth must be human-verified.
- Do not use ground truth inside the production pipeline.
- LLM-generated evidence may differ from OCR source text.
- OCR reading order can distort semantic relationships.
- Preserve source provenance and bounding boxes.
- Spatial proximity alone does not prove entity roles.
- Low-information pages must not be automatically discarded.
- Separate content relevance from processing requirements.
- Do not tune and evaluate thresholds on the same dataset.
- Measure extraction quality, latency, and cost.
- Keep business logic separate from LangGraph orchestration.

## 10. CURRENT POSITION — NEXT ACTION

We have completed offline Adaptive Routing v1/v2
development and a preliminary 15-page audit.

NEXT TASK:
Integrate Adaptive Routing v2 into the new LangGraph.

Proposed workflow:
Load Document
-> Assess and Route
-> Process Page
-> Extract Information
-> Verify Extraction
-> END

Implementation plan:
1. Add assess_and_route_node.
2. Read page quality features using page_quality.py.
3. Call choose_processing_route_v2().
4. Store routing decision and explanation in WorkflowState.
5. Support the "digital" route in process_page_node.
6. Temporarily map "review" to Tesseract fallback,
   while preserving uncertainty metadata.
7. Test routing decisions without OCR/API calls.
8. Test end-to-end graph.
9. Save metrics and results.
10. Update PROJECT_STATUS.md and create Git checkpoint.

Do not implement VLM routing or correction loops yet.

## 11. Pending Research Work

- Evaluate routing on independent documents.
- Improve digital text quality detection.
- Develop robust multi-region evidence linking.
- Add OCR/VLM fallback based on quality signals.
- Implement bounded targeted correction.
- Expand human-annotated benchmark.
- Run baseline comparisons and ablation studies.

## 12. Instructions for a Future AI Assistant

Act as a senior AI architect and MSc thesis co-supervisor.

Explain concepts and architectural decisions before coding.
Proceed step by step, avoiding unnecessary complexity.
Reuse existing modules instead of duplicating logic.
Clearly distinguish implemented, tested, and planned work.
Never assume an unseen file's contents.
Ask to inspect existing code before modifying it.
Prefer small tests using saved artifacts over repeated
OCR or paid API calls.
Keep PROJECT_STATUS.md updated frequently.
Maintain scientific rigor and reproducibility.

## Adaptive Routing Integration — 2026-10-20

Implemented:
- Page quality assessment with visual ink and Greek ratio.
- Experimental rule-based Routing Policy v2.
- assess_and_route_node.
- Routing metadata in WorkflowState.
- Digital fast path in process_page_node.
- Adaptive routing node in multimodal_graph.py.

Validated:
- Digital route:
  Document Ψ882469Β7Γ-Φ0Κ, page 1.
  2744 characters.
  Processing duration: approximately 0 seconds.

- OCR route:
  Document Ψ6ΓΧ7ΛΛ-19Χ, page 1.
  2799 characters.
  Tesseract processing duration: 12.048 seconds.

- Three-node adaptive integration test: PASS.

Important limitations:
- Routing thresholds are experimental.
- Routing accuracy has not been established independently.
- Review currently maps to Tesseract fallback.
- Full five-node adaptive graph has not been tested end-to-end.
- Verification-driven correction is not implemented.

Next:
1. Test full adaptive LangGraph with extraction and verification.
2. Define verification-driven fallback criteria.
3. Add bounded targeted correction.
4. Evaluate accuracy, latency and API cost.

---

## Checkpoint — 2026-10-26: Evidence Verification v3

### Implemented
- src/schemas/verification.py
  - EvidenceCandidate
  - ClaimVerification
- src/evaluation/evidence_retriever.py
  - Fuzzy token-based evidence retrieval
  - SourceReference preservation
- src/evaluation/claim_verifier.py
  - LLM-based semantic claim verification
  - Structured verdicts and supporting source references

### Validated
Document: Ψ882469Β7Γ-Φ0Κ, page 1.
Field: issuing_authority.
Extracted value: Πανεπιστήμιο Κρήτης - Επιτροπή Ερευνών.

Previous textual verifier:
- unsupported, score 0.684

Evidence Retrieval v1:
- Region 8: retrieval score 1.0
- Region 39: retrieval score 1.0
- Regions 24 and 27: retrieval score 0.5

Semantic Claim Verification:
- Verdict: supported
- Supporting regions: [8, 39]
- No additional OCR required

### Research Finding
Exact or fuzzy string matching alone may reject valid
claims involving Greek morphological variations.

Separating evidence retrieval from semantic claim
verification can address such cases.

Retrieval scores indicate relevance, not factual correctness.
LLM verification is not independent ground truth.

### Current Limitations
- Verification v3 is tested independently but is not yet
  integrated into the production LangGraph.
- Semantic verification has been tested on one positive case.
- Contradiction and uncertainty handling require evaluation.
- LLM explanations may be insufficiently informative.
- No automatic evidence repair or correction loop yet.
- No independent benchmark proving improvement.

### Next Milestone
Integrate Verification v3 into the existing workflow,
preserving Verification v2 as a baseline.

Then implement:
1. Bounded verification-driven correction.
2. Multimodal VLM processing and fallback.
3. Benchmark evaluation and ablation studies.
4. Real-world document intelligence demonstrator.

### Engineering Principles
- Reuse existing components.
- Avoid document-specific hardcoded rules.
- Keep retrieval, verification and correction separate.
- Prefer targeted fixes over unnecessary reprocessing.
- Maintain provenance and auditability.
- Prioritize meaningful research outcomes.
- Update PROJECT_STATUS.md after milestones.
- Commit and push tested milestones to GitHub.

---

## Checkpoint — Verification v3 Integration (2026-10-26)

### Implemented
- Semantic verification node integrated into LangGraph.
- Final verification decision resolution.
- Deterministic source-backed evidence repair.
- Preservation of original extraction and evidence.
- Field-level final decisions and evidence repair records.

### Validated
Document: Ψ882469Β7Γ-Φ0Κ, page 1.

Results:
- document_type: repair_evidence (region 7)
- issuing_authority: accept_with_evidence (regions 8, 39)
- recipient: review
- contractor: repair_evidence (region 32)
- contractor_tax_id: repair_evidence (region 32)

Verification and evidence repair integration: PASS.

The latest integration test used a mocked semantic
verification response. Real semantic verification was
previously tested separately on issuing_authority.

### Limitations
- No automatic bounded reprocessing loop yet.
- No independent benchmark for semantic verification.
- Source matching does not alone prove semantic correctness.
- Final decisions are not yet equivalent to human validation.

### Next Milestone
Implement a bounded correction controller with:
- explicit retry budget,
- targeted reprocessing,
- no unnecessary OCR for evidence-only issues,
- auditable correction decisions.

Then proceed to VLM integration and benchmark evaluation.

---

## Checkpoint — 2026-10-27: Bounded Correction Loop

### Implemented
- Deterministic correction policy with MAX_RETRIES=1.
- Correction controller LangGraph node.
- Conditional retry/finish edges.
- Retry count and correction history in WorkflowState.
- Alternative processing method selection.

### Validated
Mocked LangGraph integration test: PASS.
Processing sequence: digital -> tesseract.
Retry count: 1.
Correction history entries: 1.
Final status: completed.

### Limitations
- Real end-to-end correction retry not yet tested.
- Retry policy is conservative and experimental.
- No measured improvement in extraction accuracy yet.
- Processing metrics are not yet aggregated per attempt.
- VLM is not yet integrated into adaptive routing.

### Next Milestone
1. VLM integration into the existing processing architecture.
2. Full end-to-end multimodal workflow testing.
3. Independent benchmark and baseline comparisons.
4. Document Intelligence demonstrator.

---

## Checkpoint — 2026-10-27: Multimodal Routing v1

### Implemented
- Production VLM extractor using Qwen via Groq.
- Structured image-based extraction with PageExtraction.
- Conditional LangGraph routing for text and VLM strategies.
- Direct VLM path bypasses OCR processing.
- Unified extraction output for downstream verification.

### Validated
Real VLM extraction:
- Document: Ψ6ΓΧ7ΛΛ-19Χ, page 1.
- Model: qwen/qwen3.8-27b.
- Latency: 2.987 seconds.
- Structured extraction: PASS.
- Recipient correctly distinguished from contractor in this example.

Mocked production graph integration:
- OCR calls: 0.
- VLM calls: 1 (mocked).
- Processing method: vlm.
- Final status: completed.
- Retry count: 0.
- Direct VLM graph integration: PASS.

### Limitations
- VLM strategy selection is currently manual.
- VLM source grounding is incomplete.
- No independent accuracy benchmark yet.
- No systematic latency or cost comparison.
- Real full-graph VLM verification remains to be evaluated.
- Correction retry has not been validated end-to-end with real OCR/LLM.

### Next Milestone
1. Establish human-verified benchmark and field definitions.
2. Compare digital/OCR + LLM against direct VLM.
3. Evaluate accuracy, evidence quality, latency and cost.
4. Develop a real-world Document Intelligence demonstrator.



## Benchmark v1 - Pilot Execution & Exploratory Evaluation
Date: 2026-11-12

### Completed
- Pilot corpus: 8 PDFs, 9 annotated pages.
- Annotations: 9 JSON files, all structurally valid.
- All annotation review statuses remain `pending`.
- PDF SHA-256 hashes populated and checked by the runner.
- Two extraction strategies tested:
  - Digital Text + LLM
  - Direct VLM
- 18/18 predictions collected successfully across the initial
  and resumed runs.
- Rate-limit failures handled through a paced resume script.
- Evaluation runner implemented with 11 passing tests.
- Document-type normalization improved.
- Exploratory evaluation v2 generated.

### Exploratory Results
Digital Text + LLM:
- match: 16
- nonpresent_match: 14
- value_mismatch: 8
- status_mismatch: 7

Direct VLM:
- match: 11
- nonpresent_match: 13
- value_mismatch: 16
- status_mismatch: 5

IMPORTANT:
These are comparisons against provisional annotations.
They are NOT official ground-truth accuracy metrics.

### Confirmed Findings
1. Document 63ΤΞ46ΜΦΟΤ-ΑΟΟ:
   Direct VLM assigned the contractor's mobile number
   (6983905183) to contractor_tax_id.
   Correct AFM: 801033798.
   Error: entity-field misattribution / false evidence.

2. Document 65ΓΦ6-Θ5Μ:
   Corrupted Greek digital text layer.
   Direct VLM recovered more readable recipient text.
   The document orders allocation of funds to a company;
   it does not explicitly establish a contract award.
   Keep contractor and contractor_tax_id as not_present
   under the current annotation definition.

### Important Files
- benchmark_v1/pilot_annotations/
- benchmark_v1/scripts/run_pilot.py
- benchmark_v1/scripts/resume_pilot.py
- benchmark_v1/scripts/evaluate_pilot.py
- benchmark_v1/scripts/inspect_mismatches.py
- tests/test_evaluate_pilot.py
- evaluation_results/benchmark_v1/pilot_resumed_20261112T173616Z.json
- evaluation_results/benchmark_v1/evaluation_exploratory_v2.json
- evaluation_results/benchmark_v1/evaluation_exploratory_v2.csv

### Open Issues
- Complete human review of provisional annotations.
- Verify page-level not_present fields against source PDFs.
- Review remaining entity-role disagreements.
- Verify source grounding independently of LLM evidence.
- Define official metrics and evaluation protocol.
- Evaluate LangGraph verification/correction against baselines.
- Create an independent held-out test set.

### Next Step
Continue source-based human annotation review.
Do not calculate official accuracy until annotations
are verified and the evaluation protocol is frozen.



### Routing Experiment: Corrupted Digital Text Layer
Date: 2026-11-12

Document: data/discovery/65ΓΦ6-Θ5Μ.pdf, page 1

Finding:
The PDF renders correctly, but digital text extraction
produces corrupted Greek words.

Existing routing metrics:
- text_chars: 1799
- greek_letter_ratio: 0.8935
- suspicious_text_ratio: 0.0
- selected_route: digital

Digital extraction:
- 1800 characters
- 0.020 seconds

Tesseract OCR (300 DPI, Greek language available):
- 1300 characters
- 6.291 seconds

Diagnostic term recovery:
- ΘΥΜΙΑΝΟΣ: digital=False, OCR=True
- Διάθεση: digital=False, OCR=True
- Υπόλογο: digital=False, OCR=True
- AFM 092597210: digital=True, OCR=True

Conclusion:
Current routing metrics do not detect this corrupted
digital text layer.
Tesseract recovers substantially more readable Greek
text in this case, at higher processing cost.

Limitations:
- Single-page diagnostic, not an OCR accuracy benchmark.
- No CER/WER measured.
- OCR output still contains transcription errors.
- No evidence yet that a proposed routing rule generalizes.

Relevant file:
benchmark_v1/scripts/compare_text_layers.py

Next:
Evaluate candidate lightweight text-corruption signals
on multiple development PDFs before changing routing.py.


### Routing Diagnostics - Milestone Completed (2026-11-12)

Compared digital text extraction with Tesseract OCR
on two development PDFs.

Healthy PDF: 63ΤΞ46ΜΦΟΤ-ΑΟΟ, page 1
- Digital: 2325 chars, 0.016 s, 4/4 diagnostic terms
- Tesseract: 2160 chars, 9.756 s, 4/4 terms
- Existing routing decision: digital

Corrupted text PDF: 65ΓΦ6-Θ5Μ, page 1
- Digital: 1800 chars, 0.020 s, 1/4 terms
- Tesseract: 1300 chars, 6.291 s, 4/4 terms
- Existing routing decision: digital (undesirable)
- Text corruption affects valid Greek Unicode characters.
- Current suspicious_text_ratio fails to detect it.

Pilot routing audit:
- 8 development PDFs, page 1 inspected per document
- 7 selected digital; 1 selected tesseract
- Corrupted digital text was misrouted.

Conclusions:
- Selective routing is justified as a research question.
- No new routing rule implemented yet.
- These diagnostics do not establish OCR accuracy.
- Further validation requires additional development
  examples and independent held-out test documents.

Next research milestone:
Evaluate existing validation, semantic verification,
and bounded correction mechanisms using stored
extraction failures, without changing raw predictions.
