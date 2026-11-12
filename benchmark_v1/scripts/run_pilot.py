
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import pymupdf

from src.extraction.llm_extractor import extract_from_text
from src.extraction.vlm_extractor import extract_from_image


ANNOTATIONS = Path("benchmark_v1/pilot_annotations")
OUTPUT_DIR = Path("evaluation_results/benchmark_v1")


def load_cases():
    cases = []

    for path in sorted(ANNOTATIONS.glob("*.json")):
        annotation = json.loads(
            path.read_text(encoding="utf-8")
        )

        pdf_path = Path(annotation["document"]["pdf_path"])
        expected_hash = annotation["document"]["sha256"]

        if not pdf_path.is_file():
            raise FileNotFoundError(pdf_path)

        actual_hash = hashlib.sha256(
            pdf_path.read_bytes()
        ).hexdigest()

        if actual_hash != expected_hash:
            raise ValueError(
                f"PDF hash mismatch: {pdf_path}"
            )

        page_number = annotation["page_number"]

        with pymupdf.open(pdf_path) as doc:
            if not 1 <= page_number <= len(doc):
                raise ValueError(
                    f"Invalid page {page_number}: {pdf_path}"
                )

        cases.append({
            "annotation_id": annotation["annotation_id"],
            "pdf_path": str(pdf_path),
            "page_number": page_number,
            "review_status": annotation["review"]["status"],
            "split": annotation["document"]["split"],
        })

    return cases


def run_strategy(case, strategy):
    start = perf_counter()

    try:
        if strategy == "digital_llm":
            with pymupdf.open(case["pdf_path"]) as doc:
                text = doc[
                    case["page_number"] - 1
                ].get_text("text")

            if not text.strip():
                raise ValueError("Empty digital text layer")

            extraction = extract_from_text(text)

        elif strategy == "direct_vlm":
            extraction = extract_from_image(
                pdf_path=case["pdf_path"],
                page_number=case["page_number"],
                dpi=150,
            )
        else:
            raise ValueError(
                f"Unknown strategy: {strategy}"
            )

        return {
            "strategy": strategy,
            "status": "success",
            "latency_sec": round(
                perf_counter() - start, 3
            ),
            "prediction": extraction.model_dump(
                mode="json"
            ),
            "error": None,
        }

    except Exception as exc:
        return {
            "strategy": strategy,
            "status": "failed",
            "latency_sec": round(
                perf_counter() - start, 3
            ),
            "prediction": None,
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
            },
        }


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--strategy",
        choices=["digital_llm", "direct_vlm", "both"],
        default="both",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
    )

    args = parser.parse_args()

    cases = load_cases()

    if args.limit is not None:
        if args.limit < 1:
            parser.error("--limit must be positive")
        cases = cases[:args.limit]

    strategies = (
        ["digital_llm", "direct_vlm"]
        if args.strategy == "both"
        else [args.strategy]
    )

    print("Cases:", len(cases))
    print("Strategies:", ", ".join(strategies))

    if args.dry_run:
        for case in cases:
            print(
                case["annotation_id"],
                "|", case["review_status"],
                "|", case["pdf_path"],
            )
        print("Dry run: no model calls")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ")

    output = {
        "run_id": run_id,
        "dataset": "pilot_development",
        "evaluation_unit": "page",
        "ground_truth_scoring": "disabled",
        "strategies": strategies,
        "results": [],
    }

    output_path = OUTPUT_DIR / f"pilot_{run_id}.json"

    for case in cases:
        for strategy in strategies:
            print(
                "Running:",
                case["annotation_id"],
                strategy,
                flush=True,
            )

            result = run_strategy(case, strategy)

            output["results"].append({
                **case,
                **result,
            })

            # Save after each attempt to preserve partial results.
            output_path.write_text(
                json.dumps(
                    output,
                    ensure_ascii=False,
                    indent=2,
                ) + "\n",
                encoding="utf-8",
            )

            print(
                result["status"],
                result["latency_sec"],
                "sec",
                flush=True,
            )

    print("Saved:", output_path)
    print("Ground-truth accuracy: NOT CALCULATED")


if __name__ == "__main__":
    main()
