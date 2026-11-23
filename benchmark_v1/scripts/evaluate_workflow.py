
"""Evaluate saved adaptive workflow predictions on development annotations."""

import argparse
import json
from collections import Counter
from pathlib import Path

from benchmark_v1.scripts.evaluate_pilot import normalized_value

FIELDS = (
    "document_type",
    "issuing_authority",
    "recipient",
    "contractor",
    "contractor_tax_id",
)


def evaluate(predictions_path, annotations_dir):
    run = json.loads(predictions_path.read_text(encoding="utf-8"))

    rows = []
    missing = []

    for item in run["results"]:
        annotation_path = annotations_dir / (
            item["annotation_id"].replace(
                "_pilot_candidate_v1", ""
            ) + ".json"
        )

        if not annotation_path.exists():
            missing.append(item["annotation_id"])
            continue

        annotation = json.loads(
            annotation_path.read_text(encoding="utf-8")
        )

        if item["status"] != "success":
            missing.append(item["annotation_id"])
            continue

        prediction = item.get("prediction") or {}
        final_decisions = item.get("final_decisions") or {}

        for field in FIELDS:
            reference = annotation["fields"][field]
            predicted = prediction.get(field, {})
            decision = final_decisions.get(field, {})

            ref_status = reference["status"]
            pred_status = predicted.get("status")

            ref_value = normalized_value(
                field, reference.get("value")
            )
            pred_value = normalized_value(
                field, predicted.get("value")
            )

            status_match = ref_status == pred_status
            value_match = ref_value == pred_value

            correct = (
                status_match
                and (
                    ref_status != "present"
                    or value_match
                )
            )

            rows.append({
                "annotation_id": item["annotation_id"],
                "field": field,
                "reference_status": ref_status,
                "prediction_status": pred_status,
                "reference_value": reference.get("value"),
                "prediction_value": predicted.get("value"),
                "correct": correct,
                "final_action": decision.get("final_action"),
            })

    return {
        "kind": "development_workflow_evaluation",
        "official_accuracy_computed": False,
        "strategy": "adaptive_text_workflow",
        "source_run": str(predictions_path),
        "summary": {
            "evaluated_fields": len(rows),
            "agreement_count": sum(r["correct"] for r in rows),
            "disagreement_count": sum(not r["correct"] for r in rows),
            "final_actions": dict(Counter(
                r["final_action"] for r in rows
            )),
        },
        "missing": missing,
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument(
        "--annotations",
        type=Path,
        default=Path("benchmark_v1/pilot_annotations"),
    )
    parser.add_argument("--out", type=Path, required=True)

    args = parser.parse_args()

    report = evaluate(args.predictions, args.annotations)

    args.out.parent.mkdir(parents=True, exist_ok=True)

    output_path = args.out.with_suffix(".json")
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("DEVELOPMENT EVALUATION — NOT HELD-OUT ACCURACY")
    print(json.dumps(report["summary"], indent=2))
    print("Missing:", len(report["missing"]))
    print("Saved:", output_path)


if __name__ == "__main__":
    main()
