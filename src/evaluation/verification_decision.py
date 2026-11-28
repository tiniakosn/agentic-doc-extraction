
from dataclasses import dataclass
from typing import Any, Literal


VerificationAction = Literal[
    "accept",
    "repair_evidence",
    "reprocess",
    "review",
]


@dataclass(frozen=True)
class FieldDecision:
    action: VerificationAction
    reason: str
    decision_source: str = "verification"


def decide_field_action(
    verification: dict[str, Any],
) -> FieldDecision:
    """Classify verification signals into a next action."""

    deterministic = verification.get("deterministic_validation")

    if deterministic and deterministic.get("status") == "invalid":
        return FieldDecision(
            action="reprocess",
            reason=deterministic.get(
                "reason",
                "Deterministic validation failed",
            ),
            decision_source="deterministic_validation",
        )

    value = verification.get("value_grounding")
    evidence = verification.get("evidence_matching")
    references = verification.get("source_references", [])

    # Absence checked against field cues in the page text.
    if verification.get("verification_status") == "absence_checked":
        absence = verification.get("absence_check") or {}

        if absence.get("status") == "supported":
            return FieldDecision(
                action="accept",
                reason=absence.get("reason", "Absence supported"),
                decision_source="absence_check",
            )

        return FieldDecision(
            action="review",
            reason=absence.get("reason", "Possible missed value"),
            decision_source="absence_check",
        )


    # No asserted value or unverified absence.
    if verification.get("verification_status") == "not_checked":
        return FieldDecision(
            action="review",
            reason="Field absence or uncertainty was not verified",
        )

    if not value or not evidence:
        return FieldDecision(
            action="review",
            reason="Insufficient verification signals",
        )

    value_supported = value["status"] == "supported"
    evidence_supported = evidence["status"] == "supported"
    has_source = bool(references)

    # Value and evidence are supported.
    if value_supported and evidence_supported:
        return FieldDecision(
            action="accept",
            reason="Value and evidence are textually supported",
        )

    # Value is grounded in an actual source region,
    # but the LLM evidence string differs.
    if value_supported and has_source and not evidence_supported:
        return FieldDecision(
            action="repair_evidence",
            reason="Value anchored; evidence quotation needs repair",
        )

    # Value cannot be reliably located.
    if value["status"] == "unsupported":
        return FieldDecision(
            action="reprocess",
            reason="Extracted value not supported by source text",
        )

    return FieldDecision(
        action="review",
        reason="Verification remains ambiguous",
    )
