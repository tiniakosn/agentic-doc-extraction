from unittest.mock import patch

from src.nodes.semantic_verification import semantic_verification_node


def test_invalid_afm_skips_semantic_llm():
    state = {
        "extraction": {
            "contractor_tax_id": {
                "status": "present",
                "value": "6983905183",
                "evidence": "ΑΦΜ: 6983905183",
            }
        },
        "field_decisions": {
            "contractor_tax_id": {
                "action": "reprocess",
                "reason": "Invalid Greek AFM",
                "decision_source": "deterministic_validation",
            }
        },
        "processed_page": {
            "page_number": 1,
            "method": "digital",
            "regions": [
                {
                    "text": "ΑΦΜ: 6983905183",
                    "bbox": [0, 0, 100, 20],
                }
            ],
        },
        "document": {
            "document_id": "test_document",
        },
        "verification": {},
        "metrics": {},
    }

    with patch(
        "src.nodes.semantic_verification.verify_claim"
    ) as mock_verify:
        result = semantic_verification_node(state)

    mock_verify.assert_not_called()

    assert result["final_decisions"]["contractor_tax_id"][
        "final_action"
    ] == "reprocess"