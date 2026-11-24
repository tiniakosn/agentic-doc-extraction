
from unittest.mock import patch

import pytest

from src.evaluation.document_verifier import verify_document_field
from src.schemas.document_extraction import (
    DocumentExtraction,
    DocumentField,
    PageFieldEvidence,
)
from src.schemas.verification import ClaimVerification


def make_document():
    return DocumentExtraction(
        document_id="corinth_test",
        page_count=2,
        fields={
            "recipient": DocumentField(
                status="present",
                value="Πρωτοδικείο Κορίνθου",
                sources=[
                    PageFieldEvidence(
                        page_number=2,
                        value="Πρωτοδικείο Κορίνθου",
                        evidence="Τελικός φορέας",
                    )
                ],
            ),
            "contractor": DocumentField(
                status="present",
                value="ΑΛΦΑ",
                sources=[
                    PageFieldEvidence(
                        page_number=2,
                        value="ΑΛΦΑ",
                        evidence="Αναθέτουμε στην επιχείρηση ΑΛΦΑ",
                    )
                ],
            ),
        },
    )


def test_document_verification_uses_all_pages():
    document = make_document()

    page_texts = {
        1: (
            "ΠΡΩΤΟΔΙΚΕΙΟ ΚΟΡΙΝΘΟΥ "
            "για τον τελικό Φορέα ΠΡΩΤΟΔΙΚΕΙΟ ΚΟΡΙΝΘΟΥ"
        ),
        2: (
            "Αναθέτουμε στην επιχείρηση ΑΛΦΑ "
            "για τις ανάγκες του Πρωτοδικείου Κορίνθου"
        ),
    }

    fake_result = ClaimVerification(
        field_name="recipient",
        claimed_value="Πρωτοδικείο Κορίνθου",
        verdict="insufficient_evidence",
        explanation="No explicit recipient designation",
        verification_method="mock_document_verification",
    )

    with patch(
        "src.evaluation.document_verifier.verify_claim",
        return_value=fake_result,
    ) as mock_verify:

        result = verify_document_field(
            extraction=document,
            field_name="recipient",
            page_texts=page_texts,
            page_methods={
                1: "digital",
                2: "digital",
            },
        )

    assert result.verdict == "insufficient_evidence"

    kwargs = mock_verify.call_args.kwargs

    assert kwargs["field_name"] == "recipient"

    anchors = kwargs["text_anchors"]

    assert {a["page_number"] for a in anchors} == {1, 2}
    assert all(
        a["document_id"] == "corinth_test"
        for a in anchors
    )
    assert all(
        a["method"] == "digital"
        for a in anchors
    )


def test_document_verification_rejects_incomplete_pages():
    document = make_document()

    with pytest.raises(ValueError):
        verify_document_field(
            extraction=document,
            field_name="recipient",
            page_texts={1: "ΠΡΩΤΟΔΙΚΕΙΟ ΚΟΡΙΝΘΟΥ"},
        )


def test_document_conflict_is_not_sent_to_llm():
    document = make_document()
    document.fields["recipient"].status = "conflict"
    document.fields["recipient"].value = None

    with patch(
        "src.evaluation.document_verifier.verify_claim"
    ) as mock_verify:

        result = verify_document_field(
            extraction=document,
            field_name="recipient",
            page_texts={
                1: "Κείμενο πρώτης σελίδας",
                2: "Κείμενο δεύτερης σελίδας",
            },
        )

    mock_verify.assert_not_called()
    assert result.verdict == "not_checked"
    assert result.verification_method == "document_conflict"
