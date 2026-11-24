
from src.evaluation.claim_verifier import verify_claim
from src.evaluation.document_evidence_selector import (
    select_role_evidence,
)
from src.schemas.document_extraction import DocumentExtraction
from src.schemas.verification import ClaimVerification


SUPPORTED_ROLE_FIELDS = {
    "recipient",
    "contractor",
}


def verify_document_field(
    extraction: DocumentExtraction,
    field_name: str,
    page_texts: dict[int, str],
    *,
    page_methods: dict[int, str] | None = None,
    context_chars: int = 250,
    max_total_matches: int = 10,
    model_name: str = "qwen/qwen3.8-27b",
) -> ClaimVerification:
    """Verify one document-level role using evidence from all pages."""

    if field_name not in SUPPORTED_ROLE_FIELDS:
        raise ValueError(
            f"Unsupported document-level role: {field_name}"
        )

    expected_pages = set(range(1, extraction.page_count + 1))

    if set(page_texts) != expected_pages:
        raise ValueError(
            "Complete page text is required for document-level verification"
        )

    field = extraction.fields[field_name]

    if field.status == "conflict":
        return ClaimVerification(
            field_name=field_name,
            claimed_value=None,
            verdict="not_checked",
            explanation=(
                "Conflicting page-level values must be resolved "
                "before semantic verification."
            ),
            verification_method="document_conflict",
        )

    if field.status != "present" or not field.value:
        return ClaimVerification(
            field_name=field_name,
            claimed_value=None,
            verdict="not_checked",
            explanation=(
                "No unique asserted document-level value "
                "is available for verification."
            ),
            verification_method="document_field_not_present",
        )

    anchors = select_role_evidence(
        field_name=field_name,
        value=field.value,
        page_texts=page_texts,
        context_chars=context_chars,
        max_total_matches=max_total_matches,
    )

    methods = page_methods or {}

    for anchor in anchors:
        page_number = anchor["page_number"]

        anchor.update({
            "document_id": extraction.document_id,
            "method": methods.get(page_number),
        })

    if not anchors:
        return ClaimVerification(
            field_name=field_name,
            claimed_value=field.value,
            verdict="insufficient_evidence",
            explanation=(
                "No relevant text evidence was retrieved "
                "from the document."
            ),
            verification_method="document_no_evidence",
        )

    return verify_claim(
        field_name=field_name,
        claimed_value=field.value,
        candidates=[],
        text_anchors=anchors,
        model_name=model_name,
    )
