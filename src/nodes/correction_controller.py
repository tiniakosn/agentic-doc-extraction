
from src.evaluation.correction_controller import decide_correction
from src.schemas.workflow_state import WorkflowState


def correction_controller_node(state: WorkflowState) -> dict:
    retry_count = state.get("retry_count", 0)

    decision = decide_correction(
        final_decisions=state["final_decisions"],
        current_method=state["processed_page"]["method"],
        retry_count=retry_count,
        routing=state.get("routing"),
    )

    history = list(state.get("correction_history", []))

    if decision.action == "retry":
        history.append({
            "attempt": retry_count + 1,
            "previous_method": state["processed_page"]["method"],
            "next_method": decision.next_method,
            "reason": decision.reason,
            "previous_extraction": state.get("extraction"),
            "previous_verification": state.get("verification"),
            "previous_final_decisions": state.get("final_decisions"),
        })

        return {
            "processing_method": decision.next_method,
            "retry_count": retry_count + 1,
            "correction_history": history,
            "correction_action": "retry",
            "status": "retry_scheduled",
        }

    return {
        "correction_action": "finish",
        "correction_history": history,
        "status": "completed",
    }


def route_after_correction(state: WorkflowState) -> str:
    return state.get("correction_action", "finish")
