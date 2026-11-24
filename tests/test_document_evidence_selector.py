
import pytest

from src.evaluation.document_evidence_selector import (
    select_document_evidence,
    select_role_evidence,
)


def test_finds_value_on_later_page():
    pages = {
        1: "ΠΡΩΤΟΔΙΚΕΙΟ ΚΟΡΙΝΘΟΥ. Απόφαση ανάθεσης.",
        2: (
            "Αναθέτουμε στην επιχείρηση "
            "ΨΥΞΗ ΚΛΙΜΑΤΙΣΜΟΣ\nΕΞΑΕΡΙΣΜΟΣ."
        ),
    }

    anchors = select_document_evidence(
        value="ΨΥΞΗ ΚΛΙΜΑΤΙΣΜΟΣ ΕΞΑΕΡΙΣΜΟΣ",
        page_texts=pages,
    )

    assert len(anchors) == 1
    assert anchors[0]["page_number"] == 2

    anchor = anchors[0]

    assert (
        pages[2][anchor["start"]:anchor["end"]]
        == anchor["text"]
    )


def test_preserves_page_numbers_for_repeated_values():
    pages = {
        1: "Πρωτοδικείο Κορίνθου",
        2: "Ο Διευθύνων το Πρωτοδικείο Κορίνθου",
    }

    anchors = select_document_evidence(
        value="Πρωτοδικείο Κορίνθου",
        page_texts=pages,
    )

    assert [a["page_number"] for a in anchors] == [1, 2]


def test_rejects_invalid_match_limit():
    with pytest.raises(ValueError):
        select_document_evidence(
            value="ΑΛΦΑ",
            page_texts={1: "ΑΛΦΑ"},
            max_total_matches=0,
        )


def test_missing_value_returns_no_evidence():
    anchors = select_document_evidence(
        value="ΑΛΦΑ",
        page_texts={
            1: "Κείμενο πρώτης σελίδας",
            2: "Κείμενο δεύτερης σελίδας",
        },
    )

    assert anchors == []


def test_retrieves_contextual_recipient_role():
    pages = {
        1: (
            "Για τον τελικό Φορέα "
            "ΠΡΩΤΟΔΙΚΕΙΟ ΚΟΡΙΝΘΟΥ."
        )
    }

    results = select_role_evidence(
        field_name="recipient",
        value="Πρωτοδικείο Κορίνθου",
        page_texts=pages,
    )

    contextual = [
        item for item in results
        if item["evidence_type"] == "contextual_role"
    ]

    assert contextual
    assert contextual[0]["role_cue"] == "τελικό φορέα"
    assert contextual[0]["page_number"] == 1


def test_retrieves_explicit_contractor_award():
    pages = {
        1: (
            "Αναθέτουμε στην επιχείρηση "
            "ΑΛΦΑ την προμήθεια εξοπλισμού."
        )
    }

    results = select_role_evidence(
        field_name="contractor",
        value="ΑΛΦΑ",
        page_texts=pages,
    )

    role_evidence = [
        item for item in results
        if item["evidence_type"] == "role_cue"
    ]

    assert len(role_evidence) == 1
    assert role_evidence[0]["role_cue"] == (
        "Αναθέτουμε στην επιχείρηση"
    )



def test_contextual_evidence_is_preserved_with_entity_matches():
    pages = {
        1: (
            "ΠΡΩΤΟΔΙΚΕΙΟ ΚΟΡΙΝΘΟΥ. "
            "Για τον τελικό Φορέα "
            "ΠΡΩΤΟΔΙΚΕΙΟ ΚΟΡΙΝΘΟΥ."
        ),
        2: (
            "Αναθέτουμε στην επιχείρηση ΑΛΦΑ "
            "για τις ανάγκες του Πρωτοδικείου Κορίνθου."
        ),
    }

    results = select_role_evidence(
        field_name="recipient",
        value="Πρωτοδικείο Κορίνθου",
        page_texts=pages,
        max_total_matches=10,
    )

    contextual = [
        item for item in results
        if item["evidence_type"] == "contextual_role"
    ]

    assert contextual
    assert any(
        item["page_number"] == 1
        and item["role_cue"] == "τελικό φορέα"
        for item in contextual
    )

def test_phrase_matching_respects_word_boundaries():
    pages = {
        1: (
            "Αναθέτουμε στην επιχείρηση ΑΛΦΑ. "
            "Η ανάθεση στη δεύτερη εταιρεία έγινε αργότερα."
        )
    }

    results = select_role_evidence(
        field_name="contractor",
        value="ΑΛΦΑ",
        page_texts=pages,
    )

    role_evidence = [
        item for item in results
        if item["evidence_type"] == "role_cue"
    ]

    assert len(role_evidence) == 1
    assert role_evidence[0]["role_cue"] == (
        "Αναθέτουμε στην επιχείρηση"
    )