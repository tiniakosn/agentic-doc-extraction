
from typing import Any


def repair_field_evidence(
    extraction: dict[str, Any],
    verification: dict[str, Any],
    final_decisions: dict[str, Any],
) -> dict[str, Any]:
    """Create source-backed evidence repairs without modifying predictions."""

    repairs = {}

    for field_name, decision in final_decisions.items():
        if decision["final_action"] != "repair_evidence":
            continue

        field = extraction.get(field_name, {})
        checks = verification.get(field_name, {})
        references = checks.get("source_references", [])

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

    return repairs
