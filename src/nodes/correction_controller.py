from src.evaluation.correction_controller import decide_correction
from src.evaluation.correction_feedback import build_correction_feedback
from src.schemas.workflow_state import WorkflowState


def correction_controller_node(state: WorkflowState) -> dict:
    retry_count = state.get("retry_count", 0)
    reflection_enabled = state.get("reflection_enabled", True)
    current_method = state["processed_page"]["method"]

    decision = decide_correction(
        final_decisions=state["final_decisions"],
        current_method=current_method,
        retry_count=retry_count,
        routing=state.get("routing"),
        allow_reflection=reflection_enabled,
    )

    history = list(state.get("correction_history", []))

    if decision.action in ("retry", "reflect"):
        feedback = (
            build_correction_feedback(
                state.get("extraction") or {},
                state["final_decisions"],
            )
            if reflection_enabled
            else None
        )

        history.append({
            "attempt": retry_count + 1,
            "action": decision.action,
            "previous_method": current_method,
            "next_method": decision.next_method,
            "reason": decision.reason,
            "feedback": feedback,
            "previous_extraction": state.get("extraction"),
            "previous_verification": state.get("verification"),
            "previous_final_decisions": state.get("final_decisions"),
        })

        output = {
            "extraction_method": "text",
            "retry_count": retry_count + 1,
            "correction_history": history,
            "correction_action": decision.action,
            "correction_feedback": feedback,
            "status": (
                "retry_scheduled"
                if decision.action == "retry"
                else "reflection_scheduled"
            ),
        }

        # Only a retry changes how the page is read.
        if decision.action == "retry":
            output["processing_method"] = decision.next_method

        return output

    unresolved_fields = [
        field_name
        for field_name, field_decision in state["final_decisions"].items()
        if field_decision["final_action"] in ("reprocess", "review")
    ]

    final_status = (
        "review_required"
        if unresolved_fields
        else "completed"
    )

    return {
        "correction_action": "finish",
        "correction_history": history,
        "status": final_status,
    }


def route_after_correction(state: WorkflowState) -> str:
    return state.get("correction_action", "finish")