# Benchmark v1 starter pack

Files:
- `ANNOTATION_GUIDELINES.md`: policy, source evidence, dev/test split, financial semantics.
- `templates/annotation_template.json`: blank, deliberately **unverified** five-field annotation.
- `templates/financial_observation_example.json`: optional financial role example, **not ground truth**.
- `scripts/validate_annotations.py`: schema/consistency checking only (not semantic verification).

Copy these into your Codespaces repo without overwriting source annotations. Suggested canonical data location: `data/benchmark_v1/annotations/`. Choose untouched PDFs and record the frozen split before extraction experiments. To validate:

```bash
python scripts/validate_annotations.py templates/annotation_template.json
```

The validator only checks structure and cannot prove that field values are factually correct, that a PDF is new, or that a reviewer has performed the recorded review.
