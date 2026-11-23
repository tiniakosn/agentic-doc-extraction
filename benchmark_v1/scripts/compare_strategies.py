
"""Offline comparison of three development extraction strategies."""

import json
from collections import Counter
from pathlib import Path

from benchmark_v1.scripts.evaluate_pilot import (
    FIELDS,
    normalized_value,
)

ROOT = Path("evaluation_results/benchmark_v1")
ANNOTATIONS = Path("benchmark_v1/pilot_annotations")

BASELINE = ROOT / "pilot_resumed_20261112T173616Z.json"
WORKFLOW = ROOT / "workflow_pilot_20261122T153546Z.json"
OUTPUT = ROOT / "strategy_comparison_dev_v1.json"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    baseline = load_json(BASELINE)
    workflow = load_json(WORKFLOW)

    predictions = {}

    for record in baseline["results"]:
        if record["status"] != "success":
            continue

        key = (
            record["annotation_id"],
            record["strategy"],
        )
        if key in predictions:
            raise ValueError(f"Duplicate prediction: {key}")
        predictions[key] = record

    for record in workflow["results"]:
        if record["status"] != "success":
            continue

        key = (
            record["annotation_id"],
            "adaptive_text_workflow",
        )
        if key in predictions:
            raise ValueError(f"Duplicate prediction: {key}")
        predictions[key] = record

    strategies = (
        "digital_llm",
        "direct_vlm",
        "adaptive_text_workflow",
    )

    rows = []
    summary = {}

    for strategy in strategies:
        counts = Counter()

        for path in sorted(ANNOTATIONS.glob("*.json")):
            annotation = load_json(path)
            annotation_id = annotation["annotation_id"]

            if annotation["review"]["status"] != "verified":
                raise ValueError(
                    f"Unverified annotation: {annotation_id}"
                )

            record = predictions.get((annotation_id, strategy))
            if record is None:
                raise ValueError(
                    f"Missing prediction: {annotation_id}, {strategy}"
                )

            for field in FIELDS:
                reference = annotation["fields"][field]
                predicted = record["prediction"][field]

                status_match = (
                    reference["status"] == predicted["status"]
                )

                value_match = (
                    normalized_value(field, reference["value"])
                    == normalized_value(field, predicted["value"])
                )

                correct = (
                    status_match
                    and (
                        reference["status"] != "present"
                        or value_match
                    )
                )

                counts["total"] += 1
                counts["correct"] += int(correct)

                rows.append({
                    "annotation_id": annotation_id,
                    "strategy": strategy,
                    "field": field,
                    "reference_status": reference["status"],
                    "reference_value": reference["value"],
                    "prediction_status": predicted["status"],
                    "prediction_value": predicted["value"],
                    "status_match": status_match,
                    "value_match": value_match,
                    "correct": correct,
                })

        summary[strategy] = {
            "correct": counts["correct"],
            "total": counts["total"],
            "agreement_rate": round(
                counts["correct"] / counts["total"], 4
            ),
        }

    report = {
        "kind": "development_strategy_comparison",
        "official_held_out_accuracy": False,
        "evaluation_unit": "page",
        "normalization": "evaluate_pilot.normalized_value",
        "summary": summary,
        "rows": rows,
    }

    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("=== DEVELOPMENT STRATEGY COMPARISON ===")

    for strategy, values in summary.items():
        print(
            strategy,
            f'{values["correct"]}/{values["total"]}',
            f'({values["agreement_rate"]:.1%})',
        )

    print("\nSaved:", OUTPUT)
    print("Held-out accuracy: NOT COMPUTED")


if __name__ == "__main__":
    main()
