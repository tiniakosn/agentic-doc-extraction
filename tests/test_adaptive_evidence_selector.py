
import json

import pytest

from src.evaluation.adaptive_evidence_selector import (
    retrieve_candidates,
    deduplicate_candidates,
    rank_candidates,
    select_with_budget,
    select_adaptive_evidence,
)


def word_counter(text: str) -> int:
    """Deterministic test counter, not a production tokenizer."""
    return len(text.split())


def test_retrieves_candidates_from_multiple_pages():
    pages = {
        1: "ΑΛΦΑ " * 15,
        2: "Αναθέτουμε στην επιχείρηση ΑΛΦΑ.",
        3: "Η επιχείρηση ΑΛΦΑ αναλαμβάνει την προμήθεια.",
    }

    candidates = retrieve_candidates(
        field_name="contractor",
        value="ΑΛΦΑ",
        page_texts=pages,
        max_candidates_per_page=20,
    )

    assert {item["page_number"] for item in candidates} == {
        1, 2, 3
    }


def test_deduplicates_overlapping_same_type_evidence():
    candidates = [
        {
            "page_number": 1,
            "start": 0,
            "end": 25,
            "evidence_type": "role_cue",
            "text": "Αναθέτουμε στην επιχείρηση",
        },
        {
            "page_number": 1,
            "start": 0,
            "end": 11,
            "evidence_type": "role_cue",
            "text": "Αναθέτουμε",
        },
        {
            "page_number": 1,
            "start": 0,
            "end": 25,
            "evidence_type": "entity_value",
            "text": "Αναθέτουμε στην επιχείρηση",
        },
    ]

    result = deduplicate_candidates(candidates)

    assert len(result) == 2
    assert any(
        item["evidence_type"] == "entity_value"
        for item in result
    )


def test_rank_prioritizes_role_evidence():
    candidates = [
        {
            "page_number": 1,
            "start": 0,
            "evidence_type": "entity_value",
            "context": "ΑΛΦΑ",
        },
        {
            "page_number": 2,
            "start": 0,
            "evidence_type": "role_cue",
            "context": "Αναθέτουμε στην επιχείρηση ΑΛΦΑ",
        },
        {
            "page_number": 3,
            "start": 0,
            "evidence_type": "contextual_role",
            "context": "ΑΛΦΑ για τις ανάγκες της υπηρεσίας",
        },
    ]

    ranked = rank_candidates(
        candidates,
        claimed_value="ΑΛΦΑ",
    )

    assert ranked[0]["evidence_type"] == "role_cue"


def test_selection_respects_token_budget():
    candidates = [
        {
            "page_number": 1,
            "start": 0,
            "end": 10,
            "evidence_type": "role_cue",
            "relevance_score": 4,
            "context": "Αναθέτουμε στην επιχείρηση ΑΛΦΑ",
        },
        {
            "page_number": 2,
            "start": 20,
            "end": 30,
            "evidence_type": "entity_value",
            "relevance_score": 1,
            "context": "ΑΛΦΑ",
        },
    ]

    result = select_with_budget(
        candidates,
        token_budget=1000,
        token_counter=word_counter,
    )

    assert result["estimated_tokens"] <= 1000
    assert result["selection_metadata"]["budget_exceeded"] is False


def test_selection_preserves_page_coverage():
    candidates = []

    for page in range(1, 5):
        candidates.append({
            "page_number": page,
            "start": 0,
            "end": 10,
            "evidence_type": "role_cue",
            "relevance_score": 3,
            "context": f"Evidence page {page}",
        })

        for index in range(4):
            candidates.append({
                "page_number": page,
                "start": 20 + index * 10,
                "end": 25 + index * 10,
                "evidence_type": "entity_value",
                "relevance_score": 1,
                "context": f"Entity page {page} {index}",
            })

    result = select_with_budget(
        candidates,
        token_budget=1000,
        token_counter=word_counter,
        max_selected=8,
        max_per_page=2,
    )

    assert result["page_coverage"] == [1, 2, 3, 4]
    assert result["selected_count"] == 8

    for count in result["selection_metadata"][
        "per_page_selected_counts"
    ].values():
        assert count <= 2


def test_budget_never_selects_oversized_evidence():
    candidates = [{
        "page_number": 1,
        "start": 0,
        "end": 100,
        "evidence_type": "role_cue",
        "relevance_score": 3,
        "context": "A " * 500,
    }]

    result = select_with_budget(
        candidates,
        token_budget=1,
        token_counter=word_counter,
    )

    assert result["selected_evidence"] == []
    assert result["selected_count"] == 0
    assert result["selection_metadata"]["budget_exceeded"] is False
    assert result["selection_metadata"]["skipped_over_budget"] == 1


def test_full_adaptive_pipeline_preserves_provenance():
    pages = {
        1: "ΠΡΟΣ: Διεύθυνση Οικονομικών Υπηρεσιών.",
        2: "Αναθέτουμε στην επιχείρηση ΑΛΦΑ την προμήθεια.",
    }

    result = select_adaptive_evidence(
        field_name="contractor",
        value="ΑΛΦΑ",
        page_texts=pages,
        token_budget=1000,
        token_counter=word_counter,
    )

    assert result["total_candidates"] > 0
    assert result["selected_count"] > 0

    for item in result["selected_evidence"]:
        assert item["page_number"] in pages
        assert pages[item["page_number"]][
            item["start"]:item["end"]
        ] == item["text"]


def test_rejects_invalid_budget():
    with pytest.raises(ValueError):
        select_with_budget(
            [],
            token_budget=0,
            token_counter=word_counter,
        )

def test_entity_matches_do_not_exhaust_role_evidence_budget():
    pages = {
        1: (
            ("ΑΛΦΑ " * 30)
            + "Αναθέτουμε στην επιχείρηση ΒΗΤΑ "
            "την προμήθεια εξοπλισμού."
        )
    }

    candidates = retrieve_candidates(
        field_name="contractor",
        value="ΑΛΦΑ",
        page_texts=pages,
        max_candidates_per_page=5,
    )

    entity_candidates = [
        item for item in candidates
        if item["evidence_type"] == "entity_value"
    ]

    role_candidates = [
        item for item in candidates
        if item["evidence_type"] == "role_cue"
    ]

    assert len(entity_candidates) == 5
    assert role_candidates