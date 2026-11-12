import csv
from collections import Counter
from pathlib import Path

REPORT = Path(
    "evaluation_results/benchmark_v1/"
    "evaluation_exploratory_v2.csv"
)

with REPORT.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

mismatches = [
    row for row in rows
    if row["category"] in ("value_mismatch", "status_mismatch")
]

print("Total mismatches:", len(mismatches))

counts = Counter(
    (row["strategy"], row["field"])
    for row in mismatches
)

print("\nMISMATCHES BY STRATEGY AND FIELD")
for (strategy, field), count in sorted(counts.items()):
    print(f"{strategy:12} | {field:20} | {count}")

print("\nDOCUMENT TYPE MISMATCHES")
for row in mismatches:
    if row["field"] != "document_type":
        continue

    print("\nDocument:", row["annotation_id"])
    print("Strategy:", row["strategy"])
    print("Reference:", row["reference_value"])
    print("Prediction:", row["prediction_value"])