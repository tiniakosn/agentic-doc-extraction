
from unittest.mock import patch

from src.nodes.semantic_verification import semantic_verification_node
from src.schemas.verification import ClaimVerification


def test_semantic_verification_uses_text_anchors():
    state = {
        "extraction": {
            "contractor": {
                "status": "present",
                "value": "ΑΛΦΑ",
                "evidence": "Αναθέτουμε στην εταιρεία ΑΛΦΑ",
            }
        },
        "field_decisions": {
            "contractor": {
                "action": "review",
                "reason": "Role requires verification",
                "decision_source": "verification",
            }
        },
        "processed_page": {
            "page_number": 1,
            "method": "digital",
            "text": "Αναθέτουμε στην εταιρεία ΑΛΦΑ.",
            "regions": [],
        },
        "document": {
            "document_id": "test_document",
        },
        "verification": {},
        "metrics": {},
    }

    fake_result = ClaimVerification(
        field_name="contractor",
        claimed_value="ΑΛΦΑ",
        verdict="supported",
        explanation="Explicit award in source context",
        verification_method="mock_semantic",
    )

    with patch(
        "src.nodes.semantic_verification.verify_claim",
        return_value=fake_result,
    ) as mock_verify:
        result = semantic_verification_node(state)

    mock_verify.assert_called_once()

    kwargs = mock_verify.call_args.kwargs

    assert kwargs["candidates"] == []
    assert len(kwargs["text_anchors"]) == 1
    assert "Αναθέτουμε" in kwargs["text_anchors"][0]["context"]

    assert result["semantic_verification"]["contractor"]["verdict"] == "supported"



from src.evaluation.correction_controller import decide_correction


def test_accepted_contractor_can_be_flagged_for_review():
    state = {
        "extraction": {
            "contractor": {
                "status": "present",
                "value": "ΑΛΦΑ",
                "evidence": "Διάθεση ποσού στην εταιρεία ΑΛΦΑ",
            }
        },
        "field_decisions": {
            "contractor": {
                "action": "accept",
                "reason": "Value and evidence are textually supported",
                "decision_source": "verification",
            }
        },
        "processed_page": {
            "page_number": 1,
            "method": "digital",
            "text": "Εγκρίνεται η διάθεση ποσού στην εταιρεία ΑΛΦΑ.",
            "regions": [],
        },
        "document": {
            "document_id": "test_document",
        },
        "verification": {},
        "metrics": {},
    }

    fake_result = ClaimVerification(
        field_name="contractor",
        claimed_value="ΑΛΦΑ",
        verdict="contradicted",
        explanation="No explicit award or concluded contract",
        verification_method="mock_semantic",
    )

    with patch(
        "src.nodes.semantic_verification.verify_claim",
        return_value=fake_result,
    ) as mock_verify:
        result = semantic_verification_node(state)

    mock_verify.assert_called_once()

    final = result["final_decisions"]["contractor"]

    assert final["initial_action"] == "accept"
    assert final["final_action"] == "review"
    assert final["semantic_verdict"] == "contradicted"

    correction = decide_correction(
        final_decisions=result["final_decisions"],
        current_method="digital",
        retry_count=0,
    )

    assert correction.action == "finish"



def test_accepted_role_without_evidence_requires_review():
    state = {
        "extraction": {
            "contractor": {
                "status": "present",
                "value": "ΑΛΦΑ",
                "evidence": "ΑΛΦΑ",
            }
        },
        "field_decisions": {
            "contractor": {
                "action": "accept",
                "reason": "Initially textually supported",
                "decision_source": "verification",
            }
        },
        "processed_page": {
            "page_number": 1,
            "method": "digital",
            "text": "Απόφαση για προμήθεια εξοπλισμού.",
            "regions": [],
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

    final = result["final_decisions"]["contractor"]

    assert final["final_action"] == "review"
    assert final["semantic_verdict"] == "insufficient_evidence"


