# Multimodal Agentic Document Extraction

MSc thesis project focused on reliable information extraction
from Greek administrative and public procurement documents.

## Architecture

LangGraph workflow:
Load -> Assess & Route -> Process -> Extract -> Verify

## Implemented
- PDF ingestion with PyMuPDF
- Digital text and OCR processing
- Experimental adaptive routing
- Structured extraction using Qwen
- Source-anchored evidence
- Textual verification and field-level decisions
- Experimental semantic claim verification

## In Progress
- Verification v3 integration
- Bounded correction loop
- VLM integration
- Benchmark evaluation
- Document Intelligence demonstrator

## Project Status

See PROJECT_STATUS.md for implementation details,
research findings, limitations and next steps.
