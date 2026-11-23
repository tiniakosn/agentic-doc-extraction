
import pytest

from src.evaluation.document_aggregator import aggregate_document
from src.schemas.page_extraction import PageExtraction


def make_page(authority, contractor=None):
    return PageExtraction.model_validate({
        "document_type": {
            "status": "present",
            "value": "ΑΝΑΘΕΣΗ ΠΡΟΜΗΘΕΙΑΣ",
            "evidence": "ΑΝΑΘΕΣΗ ΠΡΟΜΗΘΕΙΑΣ",
        },
        "issuing_authority": {
            "status": "present",
            "value": authority,
            "evidence": authority,
        },
        "recipient": {
            "status": "not_present",
            "value": None,
        },
        "contractor": (
            {
                "status": "present",
                "value": contractor,
                "evidence": f"Αναθέτουμε στην επιχείρηση {contractor}",
            }
            if contractor
            else {
                "status": "not_present",
                "value": None,
            }
        ),
        "contractor_tax_id": {
            "status": "not_present",
            "value": None,
        },
    })


def test_aggregates_contractor_from_second_page():
    pages = {
        1: make_page("ΠΡΩΤΟΔΙΚΕΙΟ ΚΟΡΙΝΘΟΥ"),
        2: make_page(
            "Πρωτοδικείο Κορίνθου",
            contractor="ΨΥΞΗ ΚΛΙΜΑΤΙΣΜΟΣ ΕΞΑΕΡΙΣΜΟΣ",
        ),
    }

    result = aggregate_document(
        document_id="test_document",
        page_count=2,
        page_extractions=pages,
    )

    assert result.fields["issuing_authority"].status == "present"
    assert len(result.fields["issuing_authority"].sources) == 2

    contractor = result.fields["contractor"]

    assert contractor.status == "present"
    assert contractor.sources[0].page_number == 2
    assert contractor.value == "ΨΥΞΗ ΚΛΙΜΑΤΙΣΜΟΣ ΕΞΑΕΡΙΣΜΟΣ"


def test_rejects_incomplete_document():
    with pytest.raises(ValueError):
        aggregate_document(
            document_id="test_document",
            page_count=2,
            page_extractions={
                1: make_page("Πρωτοδικείο Κορίνθου")
            },
        )
