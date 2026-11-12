# Benchmark v1 — Annotation Guidelines

**Status:** Draft v1, for independent human review. **No pre-existing annotation is automatically ground truth.**

## Purpose and unit of evaluation

The initial task is to extract five fields (`document_type`, `issuing_authority`, `recipient`, `contractor`, `contractor_tax_id`) from Greek public-administration and procurement PDFs. Use **document-level** labels for the primary benchmark: review the **entire PDF** before deciding a field is absent. A page-level annotation is permissible only when `scope="page"`, `page_number` is specified, and the metric is explicitly page-level; do not pool page- and document-level scores. Keep documents used during development/tuning in `dev`; select distinct unseen PDFs for `test` **before** running systems or viewing their predictions. A document and all its pages belong to the same split. Record the original PDF SHA-256 to detect duplicates.

## Field definitions

- `document_type`: semantic type of the **current document** (e.g., `award_decision`, `invitation`, `other`, `uncertain_type`). A reference to an older award/invitation does not change the current document's type. The `value` is the canonical category. Record the source wording in evidence.
- `issuing_authority`: organization responsible for issuing this document, not every superior ministry or department in its letterhead. Choose the narrowest issuing organization clearly supported by title/signature/operative text; preserve its legal name, normalize whitespace only. Disputed granularity => `uncertain` with notes.
- `recipient`: explicitly addressed person/organization for the current document (e.g., `ΠΡΟΣ`). Multiple independent recipients are **not** silently compressed into one value: mark `uncertain` and record the list in `notes` until a multi-value schema is adopted. Do not infer recipient from bidders or copied parties.
- `contractor`: awarded economic operator in the operative decision of **this document**. An invitee, candidate, prior contractor, or mentioned firm is not automatically the selected contractor. Normalize only insignificant whitespace/typography; preserve entity spelling.
- `contractor_tax_id`: tax ID linked to the awarded contractor, not any unrelated AFM in the PDF. Preserve digits and leading zeroes as a string. Do not infer a missing AFM from external lookup.

## Status and evidence

- `present`: unequivocally supported by the document. Provide nonempty `value` and at least one exact **source excerpt**, one-based `page`, and `source_kind` (`digital`, `ocr`, `visual`). The excerpt should reproduce the source, not the model's explanation. If source extraction has encoding corruption, cite the visual passage and mark `source_kind="visual"` after opening the PDF.
- `not_present`: after reviewing the **entire agreed scope**, the field is genuinely absent or not established by this document. `value=null`, `evidence=[]`; include a concise review note describing what was checked. For an invitation with no award, `contractor=not_present` is reasonable when the whole document has been inspected. A figure appearing in a budget is not the contract award amount.
- `uncertain`: cannot reliably decide due to poor legibility, genuine ambiguity, conflicting mentions, or unresolved annotation policy. `value=null`; evidence may be supplied. Do **not** use `not_present` as a proxy for failed extraction.
- A field is **not human-verified** until a reviewer has checked the original PDF, including its visual appearance for ambiguous passages. Automated lexical matches are diagnostic only. `review.status` is `pending`, `verified`, or `rejected`; initial templates must remain `pending`.

## Optional financial roles (record separately, not in five-field primary scores)

- `awarded_total_amount`: amount awarded by the operative decision, inclusive/exclusive VAT as stated (capture VAT treatment). Distinguish from `estimated_budget`.
- `estimated_budget`: pre-award budget or authorized credit.
- `unit_rate`: cost per trip/item/service unit, with unit and VAT treatment.
- `performance_guarantee`: required guarantee, not a payment or award.
- `vat_rate`: numeric percentage only if stated unambiguously, never infer merely from 'VAT included'.

Each financial observation uses an `amount` decimal string, `currency="EUR"` if explicit, `vat_treatment` (`inclusive`, `exclusive`, `unspecified`), `unit` when relevant, and source evidence. Financial roles are **observations** and not part of the primary 5-field metrics in v1.

## Evidence quality and comparison rules

- Preserve source page numbering (1-based). Verify the exact passage visually when PDF text extraction is damaged. Do not rewrite corrupted extracted text into a claimed exact quote.
- Score `status` separately from value. For present fields, compare tax IDs with exact string match (after removing separators only per a documented rule); category labels exactly; organization/person names with a **declared** conservative normalization (Unicode NFC, casefold, whitespace, optional punctuation sensitivity). Report strict exact match as well as normalized match. Do not allow fuzzy matching alone to count as truth.
- Only `review.status="verified"` and split `test` documents count toward final held-out benchmark accuracy. Report per-field and micro/macro measures, missingness, abstention (`uncertain`) and evidence support separately. Include per-strategy runtime and tokens/cost if collected. One page or one example is not evidence of general superiority.

## Review workflow

1. Register filename, SHA-256, page count, and split; deduplicate by hash and similar source metadata.
2. Annotate **without seeing model predictions**. Read the whole document for document-level absence decisions.
3. Capture field value, status, exact excerpt, source page, and a short note for contested semantics.
4. A reviewer opens the original PDF and checks every positive excerpt and each negative decision across the scope.
5. On dispute, store the disagreement and adjudication before marking `verified`. Do not overwrite legacy source annotations; create versioned canonical records.
6. Run `scripts/validate_annotations.py` and freeze a benchmark manifest before model comparisons.

## Findings from development documents — provisional, NOT held-out scores

- `doc_001` (`data/raw/doc_1_digital.pdf`): operative award text on page 2 names `ΚΛΕΙΘΡΟΠΟΙΟΣ ΜΠΟΥΛΙΟΣ ΧΡ. ΓΙΑΝΝΑΚΗΣ`, AFM `079242023`, and total €399.90 including VAT. Legacy quotations and page attribution need correction against the visual PDF.
- `doc_002` (`data/raw/doc_2_digital.pdf`): invitation for Oinousses–Chios maritime route; €1,656.08 on page 1 is a **per complete trip** rate excluding VAT; €1,059.89 on page 4 is a performance guarantee. PDF text layer visibly has Greek-character corruption. Absence of selected contractor is provisional pending original-PDF review.
- `doc_003` (`data/raw/doc_3_digital.pdf`): award to `ΚΟΝΤΗΣ ΜΟΝΟΠΡΟΣΩΠΗ Ε.Π.Ε.`, AFM `095367575`, total €2,015 including VAT on page 2; page 1 includes €2,200 estimated budget. Legacy contractor evidence incorrectly states page 1.
- `Ψ6ΓΧ7ΛΛ-19Χ_page1.json`: only page-level development annotation; no independent visual verification established here.

The above observations came from supplied extracted-text review material, not an original-PDF visual audit. All remain `pending` until human review.
