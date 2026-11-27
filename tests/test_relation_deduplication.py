
from src.evaluation.adaptive_evidence_selector import (
    deduplicate_candidates,
)

from benchmark_v1.adaptive_evidence.relation_metrics import (
    evaluate_relations,
)

from benchmark_v1.adaptive_evidence.synthetic_generator_v2_2 import (
    generate_synthetic_document_v2_2,
)


def candidate_from_annotation(document, annotation):
    """Build a candidate with exact sentence-level context."""

    if "role_cue_start" in annotation:
        start = annotation["role_cue_start"]
        end = annotation["role_cue_end"]
        evidence_type = "role_cue"
    else:
        start = annotation["entity_start"]
        end = annotation["entity_end"]
        evidence_type = "entity_value"

    return {
        "page_number": annotation["page_number"],
        "start": start,
        "end": end,
        "evidence_type": evidence_type,
        "context": annotation["sentence"],
        "context_start": annotation["sentence_start"],
        "context_end": annotation["sentence_end"],
    }


def test_duplicate_candidates_are_removed_without_losing_relations():
    document = generate_synthetic_document_v2_2(10)

    relations = [
        item for item in document.annotations
        if item["annotation_type"] == "role_relation"
    ]

    original_candidates = [
        candidate_from_annotation(document, annotation)
        for annotation in relations
    ]

    duplicated_candidates = [
        candidate
        for original in original_candidates
        for candidate in (original, original.copy())
    ]

    deduplicated = deduplicate_candidates(
        duplicated_candidates
    )

    before = evaluate_relations(
        duplicated_candidates,
        document.annotations,
    )

    after = evaluate_relations(
        deduplicated,
        document.annotations,
    )

    assert len(duplicated_candidates) == 12
    assert len(deduplicated) == 6

    assert before["supporting_relation_recall"] == 1.0
    assert after["supporting_relation_recall"] == 1.0

    assert before["non_supporting_relation_exposure"] == 1.0
    assert after["non_supporting_relation_exposure"] == 1.0


def test_deduplication_preserves_all_positive_relations():
    document = generate_synthetic_document_v2_2(10)

    supporting = [
        item for item in document.annotations
        if item["supports_claim"]
    ]

    candidates = [
        candidate_from_annotation(document, annotation)
        for annotation in supporting
    ]

    result = deduplicate_candidates(candidates)

    metrics = evaluate_relations(
        result,
        document.annotations,
    )

    assert len(result) == 3
    assert metrics["supporting_relation_recall"] == 1.0


def test_deduplication_preserves_negative_and_ambiguous_relations():
    document = generate_synthetic_document_v2_2(10)

    non_supporting = [
        item for item in document.annotations
        if (
            item["annotation_type"] == "role_relation"
            and not item["supports_claim"]
        )
    ]

    candidates = [
        candidate_from_annotation(document, annotation)
        for annotation in non_supporting
    ]

    result = deduplicate_candidates(candidates)

    metrics = evaluate_relations(
        result,
        document.annotations,
    )

    assert metrics["non_supporting_relation_exposure"] == 1.0
