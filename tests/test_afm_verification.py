from src.evaluation.field_validation import validate_greek_afm


def test_invalid_vlm_tax_id_is_rejected():
    predicted_tax_id = "6983905183"

    assert validate_greek_afm(predicted_tax_id) is False


def test_valid_source_tax_id_is_accepted():
    source_tax_id = "801033798"

    assert validate_greek_afm(source_tax_id) is True


from src.evaluation.verification_decision import decide_field_action


def test_invalid_afm_must_not_be_accepted():
    verification = {
        "verification_status": "checked",
        "value_grounding": {
            "status": "supported",
            "score": 1.0,
        },
        "evidence_matching": {
            "status": "supported",
            "score": 1.0,
        },
        "source_references": [],
        "deterministic_validation": {
            "status": "invalid",
            "reason": "Invalid Greek AFM",
        },
    }

    decision = decide_field_action(verification)

    assert decision.action != "accept"


from src.nodes.verify_extraction import verify_extraction_node


def test_verification_node_rejects_invalid_afm():
    state = {
        "extraction": {
            "contractor_tax_id": {
                "value": "6983905183",
                "status": "present",
                "evidence": "ΑΦΜ: 6983905183",
            }
        },
        "processed_page": {
            "page_number": 1,
            "method": "digital",
            "text": "ΑΦΜ: 6983905183",
            "regions": [],
        },
        "document": {
            "document_id": "test_document",
            "pages": [],
        },
        "page_number": 1,
        "metrics": {},
    }

    result = verify_extraction_node(state)

    validation = result["verification"]["contractor_tax_id"][
        "deterministic_validation"
    ]

    assert validation["status"] == "invalid"
    assert result["field_decisions"]["contractor_tax_id"][
        "action"
    ] == "reprocess"

from src.evaluation.final_decision import resolve_final_decisions


def test_semantic_support_cannot_override_invalid_afm():
    field_decisions = {
        "contractor_tax_id": {
            "action": "reprocess",
            "reason": "Invalid Greek AFM format or checksum",
            "decision_source": "deterministic_validation",
        }
    }

    semantic_verification = {
        "contractor_tax_id": {
            "verdict": "supported",
            "supporting_sources": [
                {"region_index": 1, "text": "ΑΦΜ: 6983905183"}
            ],
        }
    }

    result = resolve_final_decisions(
        field_decisions=field_decisions,
        semantic_verification=semantic_verification,
    )

    assert result["contractor_tax_id"]["final_action"] == "reprocess"