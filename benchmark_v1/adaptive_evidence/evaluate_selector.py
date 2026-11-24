
import argparse
import csv
import json
from pathlib import Path

from src.evaluation.adaptive_evidence_selector import (
    retrieve_candidates,
    deduplicate_candidates,
    rank_candidates,
    select_with_budget,
)

from benchmark_v1.adaptive_evidence.metrics import (
    evaluate_evidence,
    calculate_deduplication_rate,
    calculate_budget_utilization,
)

from benchmark_v1.adaptive_evidence.synthetic_generator import (
    generate_synthetic_suite,
)


def word_counter(text: str) -> int:
    """
    Deterministic whitespace counter.

    This is an experimental proxy, NOT a model tokenizer.
    """
    return len(text.split())


def evaluate_document(
    document,
    *,
    token_budget: int,
    max_selected: int,
    max_per_page: int,
) -> dict:

    field_name = "contractor"
    value = "ΑΛΦΑ"

    raw_candidates = retrieve_candidates(
        field_name=field_name,
        value=value,
        page_texts=document.page_texts,
        max_candidates_per_page=20,
    )

    deduplicated = deduplicate_candidates(raw_candidates)

    ranked = rank_candidates(
        deduplicated,
        claimed_value=value,
    )

    # Baseline: preserve retrieval ordering.
    baseline_candidates = [
        {
            **candidate,
            "relevance_score": 0.0,
        }
        for candidate in deduplicated
    ]

    baseline = select_with_budget(
        baseline_candidates,
        token_budget=token_budget,
        token_counter=word_counter,
        max_selected=max_selected,
        max_per_page=max_per_page,
    )

    adaptive = select_with_budget(
        ranked,
        token_budget=token_budget,
        token_counter=word_counter,
        max_selected=max_selected,
        max_per_page=max_per_page,
    )

    gold = document.gold_evidence

    raw_metrics = evaluate_evidence(
        raw_candidates,
        gold,
    )

    deduplicated_metrics = evaluate_evidence(
        deduplicated,
        gold,
    )

    baseline_metrics = evaluate_evidence(
        baseline["selected_evidence"],
        gold,
    )

    adaptive_metrics = evaluate_evidence(
        adaptive["selected_evidence"],
        gold,
    )

    return {
        "document_id": document.document_id,
        "page_count": document.page_count,
        "gold_evidence_count": len(gold),
        "raw_retrieval": raw_metrics,
        "deduplicated": deduplicated_metrics,
        "baseline_selection": {
            **baseline_metrics,
            "selected_count": baseline["selected_count"],
            "estimated_tokens": baseline["estimated_tokens"],
            "budget_utilization": calculate_budget_utilization(
                baseline["estimated_tokens"],
                token_budget,
            ),
        },
        "adaptive_selection": {
            **adaptive_metrics,
            "selected_count": adaptive["selected_count"],
            "estimated_tokens": adaptive["estimated_tokens"],
            "budget_utilization": calculate_budget_utilization(
                adaptive["estimated_tokens"],
                token_budget,
            ),
        },
        "deduplication_rate": calculate_deduplication_rate(
            len(raw_candidates),
            len(deduplicated),
        ),
        "selection_metadata": adaptive["selection_metadata"],
    }


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--token-budget",
        type=int,
        default=500,
    )

    parser.add_argument(
        "--max-selected",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--max-per-page",
        type=int,
        default=3,
    )

    args = parser.parse_args()

    if args.token_budget < 1:
        parser.error("--token-budget must be positive")

    if args.max_selected < 1 or args.max_per_page < 1:
        parser.error("Selection limits must be positive")

    documents = generate_synthetic_suite()

    results = [
        evaluate_document(
            document,
            token_budget=args.token_budget,
            max_selected=args.max_selected,
            max_per_page=args.max_per_page,
        )
        for document in documents
    ]

    output_dir = Path(
        "benchmark_v1/adaptive_evidence/results"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "benchmark": "adaptive_evidence_synthetic_v1",
        "evaluation_type": "synthetic_offline",
        "token_estimator": (
            "whitespace_word_proxy_not_actual_model_tokens"
        ),
        "configuration": {
            "token_budget": args.token_budget,
            "max_selected": args.max_selected,
            "max_per_page": args.max_per_page,
        },
        "documents": results,
    }

    json_path = output_dir / "evaluation_v1.json"

    json_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    csv_path = output_dir / "evaluation_v1.csv"

    with csv_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle)

        writer.writerow([
            "document_id",
            "page_count",
            "raw_candidate_count",
            "raw_precision",
            "raw_recall",
            "deduplication_rate",
            "baseline_selected_recall",
            "adaptive_selected_recall",
            "adaptive_page_coverage",
            "adaptive_estimated_tokens",
            "adaptive_budget_utilization",
        ])

        for item in results:
            writer.writerow([
                item["document_id"],
                item["page_count"],
                item["raw_retrieval"]["candidate_count"],
                item["raw_retrieval"]["precision"],
                item["raw_retrieval"]["recall"],
                item["deduplication_rate"],
                item["baseline_selection"]["recall"],
                item["adaptive_selection"]["recall"],
                item["adaptive_selection"]["page_coverage"],
                item["adaptive_selection"]["estimated_tokens"],
                item["adaptive_selection"]["budget_utilization"],
            ])

    print("=== ADAPTIVE EVIDENCE EVALUATION ===")

    for item in results:
        print(f"\nDocument: {item['document_id']}")
        print("Pages:", item["page_count"])
        print(
            "Raw candidates:",
            item["raw_retrieval"]["candidate_count"],
        )
        print(
            "Raw precision:",
            item["raw_retrieval"]["precision"],
        )
        print(
            "Raw recall:",
            item["raw_retrieval"]["recall"],
        )
        print(
            "Deduplication rate:",
            item["deduplication_rate"],
        )
        print(
            "Baseline selected recall:",
            item["baseline_selection"]["recall"],
        )
        print(
            "Adaptive selected recall:",
            item["adaptive_selection"]["recall"],
        )
        print(
            "Adaptive page coverage:",
            item["adaptive_selection"]["page_coverage"],
        )
        print(
            "Budget utilization:",
            item["adaptive_selection"]["budget_utilization"],
        )

    print("\nSaved JSON:", json_path)
    print("Saved CSV:", csv_path)
    print("API calls: 0")


if __name__ == "__main__":
    main()
