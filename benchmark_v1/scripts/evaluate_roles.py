
import json
from datetime import datetime, timezone
from pathlib import Path

import pymupdf

from src.evaluation.claim_verifier import verify_claim
from src.evaluation.text_evidence_anchor import find_text_anchors

RUN_PATH = Path(
    "evaluation_results/benchmark_v1/"
    "pilot_resumed_20261112T173616Z.json"
)

OUTPUT_DIR = Path("evaluation_results/benchmark_v1")

CASES = [
    ("65ΓΦ6-Θ5Μ", 1, "contractor"),
    ("ΕΟΣΩ46ΨΖΣΠ-ΠΣΜ", 1, "recipient"),
    ("ΨΓΥΖ4ΧΡ-3Θ3", 2, "contractor"),
]


def main():
    run = json.loads(RUN_PATH.read_text(encoding="utf-8"))
    results = []

    for document_id, page_number, field_name in CASES:
        item = next(
            r for r in run["results"]
            if r["strategy"] == "digital_llm"
            and document_id in r["annotation_id"]
            and r["page_number"] == page_number
        )

        claim = item["prediction"][field_name]

        with pymupdf.open(item["pdf_path"]) as pdf:
            source_text = pdf[page_number - 1].get_text()

        anchors = find_text_anchors(
            value=claim["value"],
            source_text=source_text,
            context_chars=250,
            max_matches=5,
        )

        if not anchors:
            results.append({
                "document_id": document_id,
                "field": field_name,
                "status": "retrieval_failed",
            })
            continue

        print(f"Verifying {document_id} / {field_name}...")

        try:
            verification = verify_claim(
                field_name=field_name,
                claimed_value=claim["value"],
                candidates=[],
                text_anchors=anchors,
            )

            results.append({
                "document_id": document_id,
                "page_number": page_number,
                "field": field_name,
                "claimed_value": claim["value"],
                "verdict": verification.verdict,
                "explanation": verification.explanation,
                "verification_method": verification.verification_method,
                "source_contexts": anchors,
            })

        except Exception as exc:
            results.append({
                "document_id": document_id,
                "page_number": page_number,
                "field": field_name,
                "status": "error",
                "error": str(exc),
            })

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    output = OUTPUT_DIR / f"role_verification_{timestamp}.json"

    output.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("\nSaved:", output)

    for result in results:
        print(
            result["document_id"],
            result["field"],
            result.get("verdict", result.get("status")),
        )


if __name__ == "__main__":
    main()
