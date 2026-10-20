
import csv
import random
from collections import defaultdict
from pathlib import Path

INPUT = Path("evaluation_results/routing_analysis.csv")
OUTPUT = Path("evaluation_results/routing_audit_labels.csv")

SEED = 42
SAMPLE_SIZE = 5


def main():
    groups = defaultdict(list)

    with INPUT.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            groups[row["route"]].append(row)

    rng = random.Random(SEED)
    records = []

    for route in ("digital", "tesseract", "review"):
        sample = rng.sample(
            groups[route],
            min(SAMPLE_SIZE, len(groups[route])),
        )

        for row in sample:
            records.append({
                "ada": row["ada"],
                "page": row["page"],
                "router_prediction": route,
                "human_label": "",
                "confidence": "",
                "notes": "",
            })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "ada",
                "page",
                "router_prediction",
                "human_label",
                "confidence",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(records)

    print("Audit samples:", len(records))
    print("Saved:", OUTPUT)


if __name__ == "__main__":
    main()
