"""Deterministic check for fields the model reported as not_present.

An absence is accepted only when the page text contains no cue that the
field could exist. This is a heuristic signal, not proof of absence.
"""
import re

from src.evaluation.field_validation import validate_greek_afm
from src.evaluation.normalization import normalized

# Patterns applied to accent-free, casefolded text (see normalization.normalized).
ROLE_CUES = {
    "recipient": (r"\bπροσ\s*:",),
    "contractor": (
        r"αναδοχ",
        r"αναθετουμε",
        r"αναθετει",
        r"κατακυρ",
    ),
}

AFM_CANDIDATE = re.compile(r"(?<!\d)\d{9}(?!\d)")


def check_absence(field_name: str, source_text: str) -> dict:
    """Return supported / cues_found / not_checkable for a not_present field."""

    if not source_text or not source_text.strip():
        return {
            "status": "not_checkable",
            "cues": [],
            "reason": "No source text available (e.g. direct VLM)",
        }

    if field_name == "contractor_tax_id":
        cues = [
            candidate
            for candidate in AFM_CANDIDATE.findall(source_text)
            if validate_greek_afm(candidate)
        ]
    elif field_name in ROLE_CUES:
        text = normalized(source_text)
        cues = [
            match.group(0)
            for pattern in ROLE_CUES[field_name]
            for match in re.finditer(pattern, text)
        ]
    else:
        return {
            "status": "not_checkable",
            "cues": [],
            "reason": "Absence of this field is unexpected; manual review",
        }

    if cues:
        return {
            "status": "cues_found",
            "cues": sorted(set(cues))[:5],
            "reason": "Page contains cues for this field; possible missed value",
        }

    return {
        "status": "supported",
        "cues": [],
        "reason": "No field cues found in page text",
    }