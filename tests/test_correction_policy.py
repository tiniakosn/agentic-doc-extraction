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