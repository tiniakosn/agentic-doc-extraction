
from typing import Any
from src.evaluation.text_evidence_anchor import find_text_anchor

def repair_field_evidence(
    extraction: dict[str, Any],
    verification: dict[str, Any],
    final_decisions: dict[str, Any],
    source_text: str = "",
) -> dict[str, Any]:
    """Create source-backed evidence repairs without modifying predictions."""

    repairs = {}

    for field_name, decision in final_decisions.items():
        field = extraction.get(field_name, {})
        checks = verification.get(field_name, {})
        references = checks.get("source_references", [])

        # Preserve the existing spatial evidence repair.
        if decision["final_action"] == "repair_evidence":
            if not references:
                continue

            source = references[0]

            repairs[field_name] = {
                "original_value": field.get("value"),
                "original_evidence": field.get("evidence"),
                "repaired_evidence": source["text"],
                "source_reference": source,
                "repair_method": "deterministic_source_anchor",
            }
            continue

        # Propose text evidence without changing a review decision.
        if decision["final_action"] != "review":
            continue

        if field.get("status") != "present":
            continue

        if checks.get("value_grounding", {}).get("status") != "supported":
            continue

        if checks.get("evidence_matching", {}).get("status") == "supported":
            continue

        anchor = find_text_anchor(
            value=field.get("value"),
            source_text=source_text,
            context_chars=40,
        )

        if anchor is None:
            continue

        repairs[field_name] = {
            "original_value": field.get("value"),
            "original_evidence": field.get("evidence"),
            "repaired_evidence": anchor["context"],
            "text_anchor": anchor,
            "source_reference": None,
            "repair_method": "text_evidence_proposal",
        }

    return repairs
