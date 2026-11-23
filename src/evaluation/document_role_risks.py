from src.schemas.document_extraction import DocumentExtraction
from src.evaluation.normalization import normalized_value


def detect_document_role_risks(
    extraction: DocumentExtraction,
) -> list[dict]:
    """Detect possible document-level role confusion."""

    risks = []

    authority = extraction.fields.get("issuing_authority")
    recipient = extraction.fields.get("recipient")

    if (
        authority is not None
        and recipient is not None
        and authority.status == "present"
        and recipient.status == "present"
    ):
        authority_value = normalized_value(
            "issuing_authority", authority.value
        )
        recipient_value = normalized_value(
            "recipient", recipient.value
        )

        if authority_value == recipient_value:
            risks.append({
                "field": "recipient",
                "risk_type": "same_as_issuing_authority",
                "reason": (
                    "Recipient and issuing authority have "
                    "the same normalized value; verify "
                    "whether the document explicitly "
                    "addresses this recipient."
                ),
                "source_pages": sorted({
                    source.page_number
                    for source in recipient.sources
                }),
            })

    return risks