BENCHMARK V1 EVALUATOR (exploratory)

Copy benchmark_v1/scripts/evaluate_pilot.py into the existing repo at the same path.
Copy tests/test_evaluate_pilot.py into the repo's tests/ directory.

From Codespaces repo root:

python -m pytest -q tests/test_evaluate_pilot.py

python -m benchmark_v1.scripts.evaluate_pilot \
  --predictions evaluation_results/benchmark_v1/pilot_resumed_20261112T173616Z.json \
  --annotations benchmark_v1/pilot_annotations \
  --out evaluation_results/benchmark_v1/evaluation_exploratory_v1

This reads only local existing files, does NOT call APIs, and writes JSON + CSV.
All counts are exploratory against candidate labels (pending), NOT verified accuracy.
Evidence warnings check format/checksum and presence in model-supplied evidence, NOT in the PDF.
Normalization is conservative; semantic name equivalence and case-by-case visual PDF review remain manual.
