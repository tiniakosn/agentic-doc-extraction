from typing import Any, TypedDict


class WorkflowState(TypedDict, total=False):
    # Input
    pdf_path: str
    page_number: int
    processing_method: str

    # Intermediate results
    document: dict[str, Any]
    processed_page: dict[str, Any]
    extraction: dict[str, Any]

    # Verification
    verification: dict[str, Any]

    # Observability
    metrics: dict[str, float]
    errors: list[str]
    status: str

    routing: dict[str, Any]