
import csv
import json
from pathlib import Path

from src.evaluation.adaptive_evidence_selector import (
    retrieve_candidates,
    deduplicate_candidates,
    rank_candidates,
    select_with_budget,
)

from benchmark_v1.adaptive_evidence.relation_metrics import (
    evaluate_relations,
)

from benchmark_v1.adaptive_evidence.synthetic_generator_v2_2 import (
    generate_synthetic_suite_v2_2,
)


TOKEN_BUDGET = 500
MAX_SELECTED = 10
MAX_PER_PAGE = 3
CONTEXT_CHARS = 250


def word_counter(text: str) -> int:
    """Deterministic offline token estimate, not a model tokenizer."""
    return len(text.split())


def evaluate_entity_mentions(
    candidates: list[dict],
    annotations: list[dict],
) -> dict:
    """Evaluate entity mention retrieval using one-to-one matching."""

    entity_candidates = [
        item for item in candidates
        if item["evidence_type"] == "entity_value"
    ]

    mentions = [
        item for item in annotations
        if item["annotation_type"] == "entity_mention"
    ]

    candidate_to_mention = {}

    def augment(mention_index, visited):
        mention = mentions[mention_index]

        for candidate_index, candidate in enumerate(entity_candidates):
            if candidate_index in visited:
                continue

            matches = (
                candidate["page_number"] == mention["page_number"]
                and candidate["start"] <= mention["entity_start"]
                and candidate["end"] >= mention["entity_end"]
            )

            if not matches:
                continue

            visited.add(candidate_index)

            previous = candidate_to_mention.get(candidate_index)

            if (
                previous is None
                or augment(previous, visited)
            ):
                candidate_to_mention[candidate_index] = mention_index
                return True

        return False

    for mention_index in range(len(mentions)):
        augment(mention_index, set())

    matched_candidates = len(candidate_to_mention)
    matched_mentions = len(set(candidate_to_mention.values()))

    precision = (
        matched_candidates / len(entity_candidates)
        if entity_candidates else 0.0
    )

    recall = (
        matched_mentions / len(mentions)
        if mentions else 0.0
    )

    return {
        "candidate_count": len(entity_candidates),
        "gold_count": len(mentions),
        "matched_candidates": matched_candidates,
        "matched_mentions": matched_mentions,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
    }


def evaluate_supporting_page_coverage(
    candidates: list[dict],
    annotations: list[dict],
) -> dict:
    """Measure page coverage of supporting role relations."""

    supporting = [
        item for item in annotations
        if (
            item["annotation_type"] == "role_relation"
            and item["supports_claim"]
        )
    ]

    gold_pages = {
        item["page_number"]
        for item in supporting
    }

    covered_pages = {
        item["page_number"]
        for item in supporting
        if any(
            candidate["page_number"] == item["page_number"]
            and candidate["context_start"] <= item["sentence_start"]
            and candidate["context_end"] >= item["sentence_end"]
            for candidate in candidates
        )
    }

    return {
        "gold_pages": sorted(gold_pages),
        "covered_pages": sorted(covered_pages),
        "page_coverage": round(
            len(covered_pages) / len(gold_pages), 4
        ) if gold_pages else 0.0,
    }


def evaluate_stage(
    candidates: list[dict],
    annotations: list[dict],
) -> dict:
    """Evaluate entity and relation retrieval at one pipeline stage."""

    return {
        "candidate_count": len(candidates),
        "entity_mentions": evaluate_entity_mentions(
            candidates,
            annotations,
        ),
        "relations": evaluate_relations(
            candidates,
            annotations,
        ),
        "supporting_page_coverage": (
            evaluate_supporting_page_coverage(
                candidates,
                annotations,
            )
        ),
    }


def evaluate_document(document: object) -> dict:
    """Execute and evaluate the complete evidence selection pipeline."""

    raw_candidates = retrieve_candidates(
        field_name="contractor",
        value=document.target_entity,
        page_texts=document.page_texts,
        context_chars=CONTEXT_CHARS,
        max_candidates_per_page=20,
    )

    deduplicated = deduplicate_candidates(raw_candidates)

    ranked = rank_candidates(
        deduplicated,
        claimed_value=document.target_entity,
    )

    selection = select_with_budget(
        ranked,
        token_budget=TOKEN_BUDGET,
        token_counter=word_counter,
        max_selected=MAX_SELECTED,
        max_per_page=MAX_PER_PAGE,
    )

    selected = selection["selected_evidence"]

    return {
        "document_id": document.document_id,
        "page_count": document.page_count,
        "gold_annotation_count": len(document.annotations),

        "raw_retrieval": evaluate_stage(
            raw_candidates,
            document.annotations,
        ),

        "deduplicated_retrieval": evaluate_stage(
            deduplicated,
            document.annotations,
        ),

        "adaptive_selection": evaluate_stage(
            selected,
            document.annotations,
        ),

        "deduplication": {
            "raw_count": len(raw_candidates),
            "deduplicated_count": len(deduplicated),
            "removed_count": (
                len(raw_candidates) - len(deduplicated)
            ),
            "removal_rate": round(
                (len(raw_candidates) - len(deduplicated))
                / len(raw_candidates),
                4,
            ) if raw_candidates else 0.0,
        },

        "selection": {
            "selected_count": selection["selected_count"],
            "estimated_tokens": selection["estimated_tokens"],
            "token_budget": TOKEN_BUDGET,
            "budget_utilization": round(
                selection["estimated_tokens"] / TOKEN_BUDGET,
                4,
            ),
            "budget_exceeded": (
                selection["selection_metadata"]["budget_exceeded"]
            ),
            "page_coverage": selection["page_coverage"],
            "metadata": selection["selection_metadata"],
        },
    }


def main():
    documents = generate_synthetic_suite_v2_2()

    results = [
        evaluate_document(document)
        for document in documents
    ]

    output_dir = Path(
        "benchmark_v1/adaptive_evidence/results"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = {
        "benchmark": "adaptive_evidence_synthetic_v2_2",
        "evaluation_type": "synthetic_offline",
        "token_estimator": "whitespace_word_proxy",
        "configuration": {
            "context_chars": CONTEXT_CHARS,
            "token_budget": TOKEN_BUDGET,
            "max_selected": MAX_SELECTED,
            "max_per_page": MAX_PER_PAGE,
        },
        "documents": results,
    }

    json_path = (
        output_dir / "evaluation_v2_2.json"
    )

    json_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    csv_path = (
        output_dir / "evaluation_v2_2.csv"
    )

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
            "raw_entity_recall",
            "raw_supporting_relation_recall",
            "raw_non_supporting_exposure",
            "deduplicated_candidates",
            "deduplication_rate",
            "deduplicated_supporting_recall",
            "selected_candidates",
            "selected_entity_recall",
            "selected_supporting_relation_recall",
            "selected_non_supporting_exposure",
            "selected_supporting_page_coverage",
            "estimated_tokens",
            "budget_utilization",
        ])

        for item in results:
            raw = item["raw_retrieval"]
            dedup = item["deduplicated_retrieval"]
            adaptive = item["adaptive_selection"]

            writer.writerow([
                item["document_id"],
                item["page_count"],
                raw["candidate_count"],
                raw["entity_mentions"]["recall"],
                raw["relations"]["supporting_relation_recall"],
                raw["relations"]["non_supporting_relation_exposure"],
                dedup["candidate_count"],
                item["deduplication"]["removal_rate"],
                dedup["relations"]["supporting_relation_recall"],
                adaptive["candidate_count"],
                adaptive["entity_mentions"]["recall"],
                adaptive["relations"]["supporting_relation_recall"],
                adaptive["relations"]["non_supporting_relation_exposure"],
                adaptive["supporting_page_coverage"]["page_coverage"],
                item["selection"]["estimated_tokens"],
                item["selection"]["budget_utilization"],
            ])

    print("=== SYNTHETIC EVIDENCE EVALUATION v2.2 ===")

    for item in results:
        print(f"\nDocument: {item['document_id']}")
        print("Pages:", item["page_count"])

        for stage_name in (
            "raw_retrieval",
            "deduplicated_retrieval",
            "adaptive_selection",
        ):
            stage = item[stage_name]

            print(f"\n{stage_name.upper()}")
            print(
                "Entity mention recall:",
                stage["entity_mentions"]["recall"],
            )
            print(
                "Supporting relation recall:",
                stage["relations"]["supporting_relation_recall"],
            )
            print(
                "Non-supporting exposure:",
                stage["relations"]["non_supporting_relation_exposure"],
            )
            print(
                "Unseen relation exposure:",
                stage["relations"]["unseen_relation_context_exposure"],
            )

        print("\nDeduplication:", item["deduplication"])
        print(
            "Supporting page coverage:",
            item["adaptive_selection"]["supporting_page_coverage"],
        )
        print("Selection:", item["selection"])

    print("\nSaved JSON:", json_path)
    print("Saved CSV:", csv_path)
    print("External API calls: 0")


if __name__ == "__main__":
    main()
