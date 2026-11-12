# Benchmark v1 — Pilot candidate annotations

**9 page-level draft annotations** from 8 documents. User confirmed that `685Κ465274-Χ1Ψ`, page 2, is genuinely blank. It is excluded from primary field-extraction scoring, while retained separately for workflow/quality testing.

All primary JSON records have `review.status=pending`, `split=dev`, `sha256=null`, and use `source_kind=visual` because the supplied source was a page rendering. They are **not human-verified ground truth**. The user should compare exact wording and roles with the ORIGINAL PDFs and fill the file hashes from the source repository before approving any label.

## Review checklist

- [ ] Confirm PDF file and one-based page number for each annotation.
- [ ] Check `document_type` category and interpretation.
- [ ] Check issuing authority granularity (especially `ΨΡ6Ξ469ΗΡΘ-7ΝΗ`).
- [ ] Check quoted `evidence.text` directly in the original PDF (source quote must be verbatim).
- [ ] Check recipient vs contractor; `91ΤΣ46ΝΙΦ6-ΠΡΛ` has an invitee AFM, not contractor AFM.
- [ ] For concluded individual service provider contracts, apply provider-inclusive contractor definition (`ΕΟΣΩ46ΨΖΣΠ-ΠΣΜ`).
- [ ] Distinguish page-level absence from full-document absence (`ΨΓΥΖ4ΧΡ-3Θ3` pages 1 and 2).
- [ ] Enter verified reviewer, timestamp, full PDF SHA-256 and page count only **after** original-page review.

Run the repository validator:

```bash
python benchmark_v1/scripts/validate_annotations.py benchmark_v1/pilot_annotations/*.json
```

Schema validation is structural only, not semantic or human validation. Keep these pilot examples in development, not held-out test.
