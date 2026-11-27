
from benchmark_v1.adaptive_evidence.relation_metrics import (
    evaluate_relations,
)

from benchmark_v1.adaptive_evidence.synthetic_generator_v2_2 import (
    generate_synthetic_document_v2_2,
)


def test_context_exposure_requires_complete_relation():
    document = generate_synthetic_document_v2_2(10)

    gold = next(
        item for item in document.annotations
        if item.get("supports_claim") is True
    )

    candidate = {
        "page_number": gold["page_number"],
        "evidence_type": "role_cue",
        "start": gold.get("role_cue_start", gold["entity_start"]),
        "end": gold.get("role_cue_end", gold["entity_end"]),
        "context_start": gold["sentence_start"],
        "context_end": gold["sentence_end"],
    }

    result = evaluate_relations(
        [candidate],
        document.annotations,
    )

    assert result["supporting_relation_recall"] == 0.3333


def test_partial_context_does_not_expose_full_relation():
    document = generate_synthetic_document_v2_2(10)

    gold = next(
        item for item in document.annotations
        if item.get("supports_claim") is True
    )

    candidate = {
        "page_number": gold["page_number"],
        "evidence_type": "role_cue",
        "start": gold["sentence_start"],
        "end": gold["sentence_start"] + 5,
        "context_start": gold["sentence_start"],
        "context_end": gold["entity_end"],
    }

    result = evaluate_relations(
        [candidate],
        document.annotations,
    )

    assert result["supporting_relation_recall"] == 0.0


def test_unseen_relation_is_exposed_without_direct_role_cue():
    document = generate_synthetic_document_v2_2(10)

    gold = next(
        item for item in document.annotations
        if item["formulation_type"] == "unseen"
    )

    candidate = {
        "page_number": gold["page_number"],
        "evidence_type": "entity_value",
        "start": gold["entity_start"],
        "end": gold["entity_end"],
        "context_start": gold["sentence_start"],
        "context_end": gold["sentence_end"],
    }

    result = evaluate_relations(
        [candidate],
        document.annotations,
    )

    assert result["unseen_relation_context_exposure"] == 1.0
    assert result["known_direct_role_cue_recall"] == 0.0


def test_duplicate_candidates_do_not_inflate_relation_recall():
    document = generate_synthetic_document_v2_2(10)

    gold = next(
        item for item in document.annotations
        if item.get("supports_claim") is True
    )

    candidate = {
        "page_number": gold["page_number"],
        "evidence_type": "role_cue",
        "start": gold["sentence_start"],
        "end": gold["sentence_end"],
        "context_start": gold["sentence_start"],
        "context_end": gold["sentence_end"],
    }

    result = evaluate_relations(
        [candidate, candidate],
        document.annotations,
    )

    assert result["supporting_relation_count"] == 3
    assert result["supporting_relation_recall"] == 0.3333


def test_empty_candidates_produce_zero_recall():
    document = generate_synthetic_document_v2_2(10)

    result = evaluate_relations(
        [],
        document.annotations,
    )

    assert result["relation_context_exposure"] == 0.0
    assert result["supporting_relation_recall"] == 0.0
