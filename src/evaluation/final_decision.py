from typing import Any


def resolve_final_decisions(
    field_decisions: dict[str, Any],
    semantic_verification: dict[str, Any],
) -> dict[str, Any]:
    """Combine deterministic and semantic verification outcomes."""

    final = {}

    for field_name, initial in field_decisions.items():
        original_action = initial["action"]
        decision_source = initial.get(
            "decision_source",
            "verification",
        )
        semantic = semantic_verification.get(field_name)

        action = original_action
        reason = initial["reason"]

        if semantic and decision_source != "deterministic_validation":
            verdict = semantic["verdict"]

            # Spatial sources OR text anchors count as supporting evidence.
            has_support = bool(
                semantic.get("supporting_sources")
                or semantic.get("supporting_text_anchors")
            )

            if verdict == "supported" and has_support:
                action = "accept_with_evidence"
                reason = "Semantic verification supports the claim"

            elif verdict == "contradicted":
                action = "review"
                reason = "Semantic verification identified a contradiction"

            elif verdict == "insufficient_evidence":
                action = "review"
                reason = "Available evidence is insufficient"

        final[field_name] = {
            "initial_action": original_action,
            "final_action": action,
            "reason": reason,
            "semantic_verdict": (
                semantic["verdict"] if semantic else None
            ),
            "supporting_sources": (
                semantic.get("supporting_sources", [])
                if semantic else []
            ),
            "supporting_text_anchors": (
                semantic.get("supporting_text_anchors", [])
                if semantic else []
            ),
            "decision_source": decision_source,
        }

    return final