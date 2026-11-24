
import json
from pathlib import Path

import pymupdf

from src.schemas.page_extraction import PageExtraction
from src.evaluation.document_aggregator import aggregate_document
from src.evaluation.document_verifier import verify_document_field


PDF_PATH = Path("data/discovery/ΨΓΥΖ4ΧΡ-3Θ3.pdf")

WORKFLOW_PATH = Path(
    "evaluation_results/benchmark_v1/"
    "workflow_pilot_20261122T153546Z.json"
)


def main():
    data = json.loads(
        WORKFLOW_PATH.read_text(encoding="utf-8")
    )

    page_extractions = {}

    for record in data["results"]:
        if (
            "ΨΓΥΖ4ΧΡ-3Θ3" in record["annotation_id"]
            and record["status"] == "success"
        ):
            page_extractions[record["page_number"]] = (
                PageExtraction.model_validate(
                    record["prediction"]
                )
            )

    with pymupdf.open(PDF_PATH) as pdf:
        page_texts = {
            index + 1: page.get_text("text")
            for index, page in enumerate(pdf)
        }

    extraction = aggregate_document(
        document_id=PDF_PATH.stem,
        page_count=len(page_texts),
        page_extractions=page_extractions,
    )

    results = {}

    for field_name in ("recipient", "contractor"):
        field = extraction.fields[field_name]

        print(f"\nVerifying: {field_name}")
        print("Claim:", field.value)

        result = verify_document_field(
            extraction=extraction,
            field_name=field_name,
            page_texts=page_texts,
            page_methods={
                1: "digital",
                2: "digital",
            },
        )

        results[field_name] = result.model_dump(mode="json")

        print("Verdict:", result.verdict)
        print("Explanation:", result.explanation)
        print(
            "Supporting pages:",
            [
                anchor.page_number
                for anchor in result.supporting_text_anchors
            ],
        )

    output_path = Path(
        "evaluation_results/benchmark_v1/"
        "corinth_document_verification_v1.json"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print("\nSaved:", output_path)


if __name__ == "__main__":
    main()
