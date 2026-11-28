from time import perf_counter

from src.extraction.llm_extractor import extract_from_text
from src.schemas.workflow_state import WorkflowState
from src.extraction.vlm_extractor import extract_from_image


def extract_information_node(state: WorkflowState) -> dict:
    start = perf_counter()

    method = state.get("extraction_method", "text")
    feedback = state.get("correction_feedback")

    if method == "vlm":
        result = extract_from_image(
            pdf_path=state["pdf_path"],
            page_number=state.get("page_number", 1),
        )
    else:
        text = state["processed_page"]["text"]
        result = (
            extract_from_text(text, feedback=feedback)
            if feedback
            else extract_from_text(text)
        )

    metrics = dict(state.get("metrics", {}))
    metrics["extraction_duration_sec"] = round(
        perf_counter() - start, 3
    )
    metrics["reflection_feedback_used"] = bool(feedback)

    output = {
        "extraction": result.model_dump(mode="json"),
        "metrics": metrics,
        "status": "extracted",
    }

    if method == "vlm":
        output["processed_page"] = {
            "page_number": state.get("page_number", 1),
            "method": "vlm",
            "text": "",
            "regions": [],
        }

    return output