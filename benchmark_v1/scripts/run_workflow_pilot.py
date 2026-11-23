
"""Run the active LangGraph on verified development pages."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
import re
import time

from groq import RateLimitError
from benchmark_v1.scripts.run_pilot import load_cases
from src.multimodal_graph import build_multimodal_graph


OUTPUT_DIR = Path("evaluation_results/benchmark_v1")


def save_results(path, data):
    """Persist progress after each case."""
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
            default=str,
        ) + "\n",
        encoding="utf-8",
    )


def parse_retry_delay(message: str) -> float | None:
    """Extract provider-suggested retry delay in seconds."""

    match = re.search(
        r"Please try again in\s+([\d.]+)\s*(ms|s)\b",
        message,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    value = float(match.group(1))
    unit = match.group(2).lower()

    return value / 1000 if unit == "ms" else value


def invoke_with_rate_limit_retry(
    graph,
    initial_state,
    max_retries: int = 3,
):
    """Retry transient rate limits with bounded backoff."""

    retries = 0

    while True:
        try:
            result = graph.invoke(initial_state)
            return result, retries

        except RateLimitError as exc:
            if retries >= max_retries:
                raise

            suggested = parse_retry_delay(str(exc))

            delay = (
                suggested + 1.0
                if suggested is not None
                else min(2 ** retries, 30)
            )

            delay = min(max(delay, 1.0), 60.0)

            retries += 1

            print(
                f"Rate limit hit. "
                f"Retry {retries}/{max_retries} "
                f"in {delay:.2f}s",
                flush=True,
            )

            time.sleep(delay)



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", type=Path, default=None)

    args = parser.parse_args()

    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")

    cases = load_cases()

    if args.limit is not None:
        cases = cases[:args.limit]

    if args.dry_run:
        print("Cases:", len(cases))
        for case in cases:
            print(case["annotation_id"])
        print("Dry run: no model calls")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.resume:
        output_path = args.resume
        output = json.loads(
            output_path.read_text(encoding="utf-8")
        )
        if output.get("dataset") != "pilot_development":
            raise ValueError("Unexpected resume dataset")
        if output.get("strategy") != "adaptive_text_workflow":
            raise ValueError("Unexpected resume strategy")
    else:
        run_id = datetime.now(timezone.utc).strftime(
            "%Y%m%dT%H%M%SZ"
        )
        output_path = OUTPUT_DIR / f"workflow_pilot_{run_id}.json"

        output = {
            "run_id": run_id,
            "dataset": "pilot_development",
            "evaluation_unit": "page",
            "strategy": "adaptive_text_workflow",
            "ground_truth_scoring": "disabled",
            "results": [],
        }

    completed = {
        item["annotation_id"]
        for item in output["results"]
        if item["status"] == "success"
    }

    graph = build_multimodal_graph()

    for case in cases:
        if case["annotation_id"] in completed:
            print("Skipping completed:", case["annotation_id"])
            continue

        print("Running:", case["annotation_id"], flush=True)

        initial_state = {
            "pdf_path": case["pdf_path"],
            "page_number": case["page_number"],
            "extraction_method": "text",
            "retry_count": 0,
        }

        start = perf_counter()

        try:
            result, api_rate_limit_retries = invoke_with_rate_limit_retry(
                graph,
                initial_state,
            )

            record = {
                **case,
                "status": "success",
                "latency_sec": round(perf_counter() - start, 3),
                "workflow_status": result.get("status"),
                "routing": result.get("routing"),
                "processing_method": result.get("processing_method"),
                "prediction": result.get("extraction"),
                "verification": result.get("verification"),
                "field_decisions": result.get("field_decisions"),
                "semantic_verification": result.get(
                    "semantic_verification"
                ),
                "final_decisions": result.get("final_decisions"),
                "evidence_repairs": result.get("evidence_repairs"),
                "retry_count": result.get("retry_count", 0),
                "correction_history": result.get(
                    "correction_history", []
                ),
                "metrics": result.get("metrics", {}),
                "error": None,
                "api_rate_limit_retries": api_rate_limit_retries,
            }

        except Exception as exc:
            record = {
                **case,
                "status": "failed",
                "latency_sec": round(perf_counter() - start, 3),
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                },
            }

        output["results"] = [
            item for item in output["results"]
            if item["annotation_id"] != case["annotation_id"]
        ]
        output["results"].append(record)

        save_results(output_path, output)

        print(
            record["status"],
            record["latency_sec"],
            "sec",
            flush=True,
        )

    print("Saved:", output_path)
    print("Ground-truth scoring: NOT CALCULATED")


if __name__ == "__main__":
    main()
