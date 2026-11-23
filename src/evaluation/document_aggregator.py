
from src.schemas.page_extraction import PageExtraction
from src.evaluation.normalization import normalized_value
from src.schemas.document_extraction import (
    DocumentExtraction,
    DocumentField,
    PageFieldEvidence,
)

FIELDS = (
    "document_type",
    "issuing_authority",
    "recipient",
    "contractor",
    "contractor_tax_id",
)


def aggregate_document(
    document_id: str,
    page_count: int,
    page_extractions: dict[int, PageExtraction],
) -> DocumentExtraction:
    """Conservatively aggregate page-level extraction results."""

    if set(page_extractions) != set(range(1, page_count + 1)):
        raise ValueError(
            "All document pages must be supplied for aggregation"
        )

    fields = {}

    for field_name in FIELDS:
        present = []
        uncertain_found = False

        for page_number, extraction in sorted(
            page_extractions.items()
        ):
            field = getattr(extraction, field_name)

            if field.status == "uncertain":
                uncertain_found = True

            if field.status == "present":
                present.append(
                    PageFieldEvidence(
                        page_number=page_number,
                        value=field.value,
                        evidence=field.evidence,
                    )
                )

        distinct_values = {
            normalized_value(field_name, source.value)
            for source in present
        }

        if len(distinct_values) > 1:
            fields[field_name] = DocumentField(
                status="conflict",
                sources=present,
                notes="Conflicting values across pages",
            )

        elif len(distinct_values) == 1:
            fields[field_name] = DocumentField(
                status="present",
                value=present[0].value,
                sources=present,
            )

        elif uncertain_found:
            fields[field_name] = DocumentField(
                status="uncertain",
                notes="At least one page is uncertain",
            )

        else:
            fields[field_name] = DocumentField(
                status="not_present",
                notes="Not established on any reviewed page",
            )

    return DocumentExtraction(
        document_id=document_id,
        page_count=page_count,
        fields=fields,
    )
