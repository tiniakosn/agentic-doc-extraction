from time import perf_counter

from src.extraction.llm_extractor import extract_from_text
from src.schemas.workflow_state import WorkflowState


def extract_information_node(state: WorkflowState) -> dict:
    start = perf_counter()

    text = state["processed_page"]["text"]
    result = extract_from_text(text)

    metrics = dict(state.get("metrics", {}))
    metrics["extraction_duration_sec"] = round(
        perf_counter() - start, 3
    )

    return {
        "extraction": result.model_dump(mode="json"),
        "metrics": metrics,
        "status": "extracted",
    }