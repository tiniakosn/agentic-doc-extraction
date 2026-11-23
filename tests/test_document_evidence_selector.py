
import pytest

from src.evaluation.document_evidence_selector import (
    select_document_evidence,
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
