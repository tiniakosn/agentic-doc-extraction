
from dataclasses import asdict
from time import perf_counter

import pymupdf

from src.ingestion.page_quality import assess_page_quality
from src.ingestion.routing import choose_processing_route_v2
from src.schemas.workflow_state import WorkflowState


def assess_and_route_node(state: WorkflowState) -> dict:
    start = perf_counter()

    pdf_path = state["pdf_path"]
    page_number = state.get("page_number", 1)

    with pymupdf.open(pdf_path) as doc:
        if not 1 <= page_number <= len(doc):
            raise ValueError(f"Invalid page number: {page_number}")

        quality = assess_page_quality(doc[page_number - 1])

    decision = choose_processing_route_v2(quality)

    # The current processing node does not support "review".
    # Temporarily execute Tesseract while retaining the
    # original routing decision for auditability.
    execution_method = (
        "tesseract"
        if decision.route == "review"
        else decision.route
    )

    metrics = dict(state.get("metrics", {}))
    metrics["routing_duration_sec"] = round(
        perf_counter() - start, 3
    )

    return {
        "processing_method": execution_method,
        "routing": {
            "decision": decision.route,
            "execution_method": execution_method,
            "reason": decision.reason,
            "quality": asdict(quality),
            "fallback_used": decision.route == "review",
        },
        "metrics": metrics,
        "status": "routed",
    }
