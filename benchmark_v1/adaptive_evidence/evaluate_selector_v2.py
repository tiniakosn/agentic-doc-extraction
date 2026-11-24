
import csv
import json
from pathlib import Path

from src.evaluation.adaptive_evidence_selector import (
    retrieve_candidates,
    deduplicate_candidates,
    rank_candidates,
    select_with_budget,
)


from benchmark_v1.adaptive_evidence.synthetic_generator_v2 import (
    generate_synthetic_suite_v2,
)

from benchmark_v1.adaptive_evidence.metrics import (
    calculate_budget_utilization,
    calculate_deduplication_rate,
    evaluate_evidence_one_to_one,
)


def word_counter(text: str) -> int:
    """Offline proxy, not an actual Qwen tokenizer."""
    return len(text.split())


def overlaps(candidate: dict, gold: dict) -> bool:
    return (
        candidate["page_number"] == gold["page_number"]
        and candidate["start"] < gold["end"]
        and candidate["end"] > gold["start"]
    )


def context_contains_span(candidate: dict, gold: dict) -> bool:
    """Check whether selected context exposes a complete gold span."""

    return (
        candidate["page_number"] == gold["page_number"]
        and candidate["context_start"] <= gold["start"]
        and candidate["context_end"] >= gold["end"]
    )


def classify_candidate(candidate, gold_evidence, target_entity):
    """Classify retrieval against the annotated synthetic ground truth."""

    matches = [
        gold for gold in gold_evidence
        if overlaps(candidate, gold)
    ]

    if not matches:
        return "unmatched"

    for gold in matches:
        if gold["evidence_type"] == "entity_value":
            return "entity"

        if gold["evidence_type"] == "role_cue":
            if target_entity.casefold() in candidate["context"].casefold():
                return "known_positive_role"

        if gold["evidence_type"] == "distractor_role_cue":
            return "distractor_role"

        if gold["evidence_type"] == "negative_role_context":
            return "negative_role"

        if gold["evidence_type"] == "contextual_role":
            return "contextual_role"

    return "unmatched"




def evaluate_retrieval(candidates, document):
    """Evaluate retrieval using category-specific one-to-one matching."""

    gold = document.gold_evidence

    gold_by_type = {
        evidence_type: [
            item for item in gold
            if item["evidence_type"] == evidence_type
        ]
        for evidence_type in {
            item["evidence_type"] for item in gold
        }
    }

    candidate_types = {
        "entity_value": "entity_value",
        "role_cue": "role_cue",
        "contextual_role": "contextual_role",
    }

    category_metrics = {}

    for gold_type, candidate_type in candidate_types.items():
        relevant_candidates = [
            item for item in candidates
            if item["evidence_type"] == candidate_type
        ]

        gold_items = gold_by_type.get(gold_type, [])

        category_metrics[gold_type] = (
            evaluate_evidence_one_to_one(
                relevant_candidates,
                gold_items,
            )
        )

    def special_retrieval_metric(gold_type):
        relevant_candidates = [
            item for item in candidates
            if item["evidence_type"] == "role_cue"
        ]

        gold_items = gold_by_type.get(gold_type, [])

        if not gold_items:
            return 0.0

        metrics = evaluate_evidence_one_to_one(
            relevant_candidates,
            gold_items,
        )

        return metrics["recall"]

    unseen_gold = gold_by_type.get(
        "unseen_role_formulation", []
    )

    unseen_direct = sum(
        any(
            candidate["page_number"] == item["page_number"]
            and candidate["start"] <= item["start"]
            and candidate["end"] >= item["end"]
            for candidate in candidates
        )
        for item in unseen_gold
    )

    unseen_context = sum(
        any(
            candidate["page_number"] == item["page_number"]
            and candidate["context_start"] <= item["start"]
            and candidate["context_end"] >= item["end"]
            for candidate in candidates
        )
        for item in unseen_gold
    )

    unseen_total = len(unseen_gold)

    return {
        "candidate_count": len(candidates),

        "entity_precision": category_metrics[
            "entity_value"
        ]["precision"],

        "entity_recall": category_metrics[
            "entity_value"
        ]["recall"],

        "known_role_precision": category_metrics[
            "role_cue"
        ]["precision"],

        "known_role_recall": category_metrics[
            "role_cue"
        ]["recall"],

        "contextual_precision": category_metrics[
            "contextual_role"
        ]["precision"],

        "contextual_recall": category_metrics[
            "contextual_role"
        ]["recall"],

        "unseen_direct_recall": round(
            unseen_direct / unseen_total, 4
        ) if unseen_total else 0.0,

        "unseen_context_exposure": round(
            unseen_context / unseen_total, 4
        ) if unseen_total else 0.0,

        "distractor_retrieval_rate": special_retrieval_metric(
            "distractor_role_cue"
        ),

        "negative_context_retrieval_rate": special_retrieval_metric(
            "negative_role_context"
        ),

        "category_metrics": category_metrics,
    }




def evaluate_document(document, config):
    field_name = "contractor"
    value = document.target_entity

    raw = retrieve_candidates(
        field_name=field_name,
        value=value,
        page_texts=document.page_texts,
        max_candidates_per_page=20,
    )

    deduplicated = deduplicate_candidates(raw)

    ranked = rank_candidates(
        deduplicated,
        claimed_value=value,
    )

    # Neutral scores: preserve a non-ranked baseline strategy.
    baseline_candidates = [
        {
            **candidate,
            "relevance_score": 0.0,
        }
        for candidate in deduplicated
    ]

    baseline = select_with_budget(
        baseline_candidates,
        token_budget=config["token_budget"],
        token_counter=word_counter,
        max_selected=config["max_selected"],
        max_per_page=config["max_per_page"],
    )

    adaptive = select_with_budget(
        ranked,
        token_budget=config["token_budget"],
        token_counter=word_counter,
        max_selected=config["max_selected"],
        max_per_page=config["max_per_page"],
    )

    raw_metrics = evaluate_retrieval(raw, document)

    dedup_metrics = evaluate_retrieval(
        deduplicated, document
    )

    baseline_metrics = evaluate_retrieval(
        baseline["selected_evidence"], document
    )

    adaptive_metrics = evaluate_retrieval(
        adaptive["selected_evidence"], document
    )

    return {
        "document_id": document.document_id,
        "page_count": document.page_count,
        "gold_evidence_count": len(document.gold_evidence),
        "raw_retrieval": raw_metrics,
        "deduplicated_retrieval": dedup_metrics,
        "baseline_selection": baseline_metrics,
        "adaptive_selection": adaptive_metrics,
        "deduplication_rate": calculate_deduplication_rate(
            len(raw), len(deduplicated)
        ),
        "baseline_selected_count": baseline["selected_count"],
        "adaptive_selected_count": adaptive["selected_count"],
        "adaptive_estimated_tokens": adaptive["estimated_tokens"],
        "budget_utilization": calculate_budget_utilization(
            adaptive["estimated_tokens"],
            config["token_budget"],
        ),
        "page_coverage": adaptive["page_coverage"],
        "selection_metadata": adaptive["selection_metadata"],
    }


def main():
    config = {
        "token_budget": 500,
        "max_selected": 10,
        "max_per_page": 3,
    }

    documents = generate_synthetic_suite_v2()

    results = [
        evaluate_document(document, config)
        for document in documents
    ]

    output_dir = Path(
        "benchmark_v1/adaptive_evidence/results"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "benchmark": "adaptive_evidence_synthetic_v2",
        "evaluation_type": "synthetic_offline",
        "token_estimator": "whitespace_word_proxy",
        "configuration": config,
        "documents": results,
    }

    json_path = output_dir / "evaluation_v2.json"

    json_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    csv_path = output_dir / "evaluation_v2.csv"

    with csv_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle)

        writer.writerow([
            "document_id",
            "pages",
            "raw_candidates",
            "entity_precision",
            "entity_recall",
            "known_role_precision",
            "known_role_recall",
            "contextual_precision",
            "contextual_recall",
            "unseen_direct_recall",
            "unseen_context_exposure",
            "distractor_retrieval_rate",
            "negative_context_retrieval_rate",
            "deduplication_rate",
            "baseline_known_role_recall",
            "adaptive_known_role_recall",
            "adaptive_budget_utilization",
            "page_coverage_count",
        ])

        for item in results:
            raw = item["raw_retrieval"]
            adaptive = item["adaptive_selection"]

            writer.writerow([
                item["document_id"],
                item["page_count"],
                raw["candidate_count"],
                raw["entity_precision"],
                raw["entity_recall"],
                raw["known_role_precision"],
                raw["known_role_recall"],
                raw["contextual_precision"],
                raw["contextual_recall"],
                raw["unseen_direct_recall"],
                raw["unseen_context_exposure"],
                raw["distractor_retrieval_rate"],
                raw["negative_context_retrieval_rate"],
                item["deduplication_rate"],
                item["baseline_selection"]["known_role_recall"],
                adaptive["known_role_recall"],
                item["budget_utilization"],
                len(item["page_coverage"]),
            ])

    for item in results:
        print("\nDOCUMENT:", item["document_id"])
        print("Pages:", item["page_count"])
        print("Raw:", item["raw_retrieval"])
        print("Deduplication:", item["deduplication_rate"])
        print("Baseline:", item["baseline_selection"])
        print("Adaptive:", item["adaptive_selection"])
        print("Page coverage:", item["page_coverage"])
        print("Budget utilization:", item["budget_utilization"])

    print("\nJSON:", json_path)
    print("CSV:", csv_path)
    print("API calls: 0")


if __name__ == "__main__":
    main()
