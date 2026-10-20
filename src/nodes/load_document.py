from pathlib import Path
from time import perf_counter

from src.ingestion.pdf_loader import load_document
from src.schemas.workflow_state import WorkflowState


def load_document_node(state: WorkflowState) -> dict:
    start = perf_counter()

    pdf_path = Path(state["pdf_path"])
    document = load_document(pdf_path)

    page_number = state.get("page_number", 1)

    if not 1 <= page_number <= len(document.pages):
        raise ValueError(f"Invalid page number: {page_number}")

    return {
        "document": document.model_dump(mode="json"),
        "status": "loaded",
        "metrics": {
            **state.get("metrics", {}),
            "load_duration_sec": round(perf_counter() - start, 3),
        },
    }