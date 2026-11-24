
from benchmark_v1.adaptive_evidence.synthetic_generator_v2 import (
    generate_synthetic_document_v2,
)

from benchmark_v1.adaptive_evidence.evaluate_selector_v2 import (
    classify_candidate,
    overlaps,
)


def test_ground_truth_overlap_uses_original_offsets():
    document = generate_synthetic_document_v2(10)

    for gold in document.gold_evidence:
        page_text = document.page_texts[gold["page_number"]]

        assert (
            page_text[gold["start"]:gold["end"]]
            == gold["text"]
        )


def test_overlap_requires_same_page():
    candidate = {
        "page_number": 1,
        "start": 10,
        "end": 20,
    }

    gold = {
        "page_number": 2,
        "start": 10,
        "end": 20,
    }

    assert overlaps(candidate, gold) is False


def test_unseen_formulation_is_not_known_positive_role():
    document = generate_synthetic_document_v2(10)

    gold = next(
        item for item in document.gold_evidence
        if item["evidence_type"] == "unseen_role_formulation"
    )

    candidate = {
        **gold,
        "evidence_type": "role_cue",
        "context": gold["text"],
    }

    assert classify_candidate(
        candidate,
        document.gold_evidence,
        document.target_entity,
    ) == "unmatched"



def test_unseen_direct_recall_differs_from_context_exposure():
    from benchmark_v1.adaptive_evidence.evaluate_selector_v2 import (
        evaluate_retrieval,
    )

    document = generate_synthetic_document_v2(10)

    result = evaluate_retrieval([], document)

    assert result["unseen_direct_recall"] == 0.0
    assert result["unseen_context_exposure"] == 0.0


def test_repeated_candidates_do_not_inflate_known_recall():
    from benchmark_v1.adaptive_evidence.evaluate_selector_v2 import (
        evaluate_retrieval,
    )

    document = generate_synthetic_document_v2(10)

    gold = next(
        item for item in document.gold_evidence
        if item["evidence_type"] == "role_cue"
    )

    candidate = {
        "page_number": gold["page_number"],
        "start": gold["start"],
        "end": gold["end"],
        "evidence_type": "role_cue",
        "context": (
            document.page_texts[gold["page_number"]]
        ),
        "context_start": 0,
        "context_end": len(
            document.page_texts[gold["page_number"]]
        ),
    }

    result = evaluate_retrieval(
        [candidate, candidate],
        document,
    )

    assert result["known_role_recall"] == 1.0

    role_metrics = result["category_metrics"]["role_cue"]

    assert role_metrics["matched_gold"] == 1
    assert role_metrics["matched_candidates"] == 1
    assert role_metrics["precision"] == 0.5
    assert role_metrics["recall"] == 1.0

def test_entity_precision_uses_only_entity_candidates():
    from benchmark_v1.adaptive_evidence.synthetic_generator_v2 import (
        generate_synthetic_document_v2,
    )
    from benchmark_v1.adaptive_evidence.evaluate_selector_v2 import (
        evaluate_retrieval,
    )

    document = generate_synthetic_document_v2(10)

    gold = next(
        item for item in document.gold_evidence
        if item["evidence_type"] == "entity_value"
    )

    candidate = {
        **gold,
        "evidence_type": "entity_value",
    }

    result = evaluate_retrieval(
        [candidate],
        document,
    )

    assert result["entity_precision"] == 1.0
    assert result["entity_recall"] > 0.0
    assert "known_positive_recall" not in result