from src.evaluation.correction_controller import decide_correction
from src.evaluation.correction_feedback import build_correction_feedback
from src.nodes.correction_controller import (
    correction_controller_node,
    route_after_correction,
)

UNSUPPORTED = {
    "contractor": {
        "final_action": "reprocess",
        "reason": "Extracted value not supported by source text",
        "decision_source": "verification",
    }
}


def test_digital_unsupported_value_triggers_reflection():
    d = decide_correction(UNSUPPORTED, current_method="digital", retry_count=0, routing={})
    assert d.action == "reflect"
    assert d.next_method == "digital"


def test_reflection_can_be_disabled_for_ablation():
    d = decide_correction(
        UNSUPPORTED, current_method="digital", retry_count=0,
        routing={}, allow_reflection=False,
    )
    assert d.action == "finish"


def test_reflection_respects_retry_budget():
    d = decide_correction(UNSUPPORTED, current_method="digital", retry_count=1, routing={})
    assert d.action == "finish"


def test_feedback_mentions_rejected_value_reason_and_hint():
    feedback = build_correction_feedback(
        {"contractor_tax_id": {"value": "6983905183"}},
        {"contractor_tax_id": {"final_action": "reprocess", "reason": "Invalid Greek AFM"}},
    )
    assert "6983905183" in feedback
    assert "Invalid Greek AFM" in feedback
    assert "9 ψηφία" in feedback


def test_no_feedback_without_rejected_fields():
    decisions = {"contractor": {"final_action": "review", "reason": "x"}}
    assert build_correction_feedback({}, decisions) is None


def test_reflect_keeps_page_and_routes_to_extraction():
    state = {
        "processed_page": {"method": "digital", "text": "κείμενο"},
        "final_decisions": UNSUPPORTED,
        "extraction": {"contractor": {"value": "ΒΗΤΑ", "status": "present", "evidence": "ΒΗΤΑ"}},
        "retry_count": 0,
        "correction_history": [],
    }

    result = correction_controller_node(state)

    assert result["correction_action"] == "reflect"
    assert "processing_method" not in result
    assert "ΒΗΤΑ" in result["correction_feedback"]
    assert route_after_correction({**state, **result}) == "reflect"