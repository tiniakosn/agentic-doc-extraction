"""Run the active multimodal LangGraph on a real PDF."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from src.multimodal_graph import build_multimodal_graph


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--pdf", required=True)
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument(
        "--strategy",
        choices=["vlm", "text"],
        default="vlm",
    )

    args = parser.parse_args()

    pdf_path = Path(args.pdf)

    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)

    output_dir = Path(
        "evaluation_results/live_correction_v1"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    initial_state = {
        "pdf_path": str(pdf_path),
        "page_number": args.page,
        "extraction_method": args.strategy,
        "retry_count": 0,
    }

    graph = build_multimodal_graph()

    result = graph.invoke(initial_state)

    output_path = output_dir / f"live_{run_id}.json"

    output_path.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print("Run ID:", run_id)
    print("Status:", result.get("status"))
    print("Retries:", result.get("retry_count", 0))
    print("Extraction method:", result.get("extraction_method"))
    print("Saved:", output_path)


if __name__ == "__main__":
    main()