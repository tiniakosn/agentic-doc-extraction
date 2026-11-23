
from src.evaluation.document_role_risks import (
    detect_document_role_risks,
)
from src.schemas.document_extraction import (
    DocumentExtraction,
    DocumentField,
    PageFieldEvidence,
)


def make_document(recipient_value):
    return DocumentExtraction(
        document_id="test_document",
        page_count=2,
        fields={
            "issuing_authority": DocumentField(
                status="present",
                value="ΠΡΩΤΟΔΙΚΕΙΟ ΚΟΡΙΝΘΟΥ",
                sources=[
                    PageFieldEvidence(
                        page_number=1,
                        value="ΠΡΩΤΟΔΙΚΕΙΟ ΚΟΡΙΝΘΟΥ",
                        evidence="ΠΡΩΤΟΔΙΚΕΙΟ ΚΟΡΙΝΘΟΥ",
                    )
                ],
            ),
            "recipient": DocumentField(
                status="present",
                value=recipient_value,
                sources=[
                    PageFieldEvidence(
                        page_number=2,
                        value=recipient_value,
                        evidence=recipient_value,
                    )
                ],
            ),
        },
    )


def test_same_authority_and_recipient_is_flagged():
    document = make_document("Πρωτοδικείο Κορίνθου")

    risks = detect_document_role_risks(document)

    assert len(risks) == 1
    assert risks[0]["field"] == "recipient"
    assert risks[0]["risk_type"] == "same_as_issuing_authority"
    assert risks[0]["source_pages"] == [2]


def test_different_recipient_is_not_flagged():
    document = make_document("Διεύθυνση Οικονομικών Υπηρεσιών")

    risks = detect_document_role_risks(document)

    assert risks == []
