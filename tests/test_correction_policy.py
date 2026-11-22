from src.evaluation.correction_controller import decide_correction


def test_vlm_cannot_retry_with_current_policy():
    decisions = {
        "contractor_tax_id": {
            "final_action": "reprocess",
            "reason": "Invalid contractor tax ID",
        }
    }

    result = decide_correction(
        final_decisions=decisions,
        current_method="vlm",
        retry_count=0,
        routing={},
    )

    assert result.action == "finish"
    assert result.next_method is None

from src.nodes.correction_controller import correction_controller_node


def test_unresolved_vlm_field_requires_review_after_retry_budget():
    state = {
        "processed_page": {
            "method": "vlm",
        },
        "final_decisions": {
            "contractor_tax_id": {
                "final_action": "reprocess",
                "decision_source": "deterministic_validation",
                "reason": "Invalid Greek AFM",
            }
        },
        "retry_count": 1,
        "correction_history": [],
    }

    result = correction_controller_node(state)

    assert result["correction_action"] == "finish"
    assert result["status"] == "review_required"

def test_invalid_vlm_afm_schedules_ocr_retry():
    state = {
        "extraction_method": "vlm",
        "processed_page": {
            "method": "vlm",
        },
        "final_decisions": {
            "contractor_tax_id": {
                "final_action": "reprocess",
                "decision_source": "deterministic_validation",
                "reason": "Invalid Greek AFM",
            }
        },
        "extraction": {
            "contractor_tax_id": {
                "value": "6983905183",
                "status": "present",
                "evidence": "ΑΦΜ: 6983905183",
            }
        },
        "retry_count": 0,
        "correction_history": [],
    }

    result = correction_controller_node(state)

    assert result["correction_action"] == "retry"
    assert result["processing_method"] == "tesseract"
    assert result["extraction_method"] == "text"
    assert result["retry_count"] == 1
    assert len(result["correction_history"]) == 1