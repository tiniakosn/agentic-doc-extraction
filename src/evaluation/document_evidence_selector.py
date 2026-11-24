
import re

from src.evaluation.text_evidence_anchor import find_text_anchors


ROLE_CUES = {
    "recipient": (
        "ΠΡΟΣ:",
    ),
    "contractor": (
        "Αναθέτουμε στην επιχείρηση",
        "Αναθέτουμε στη",
        "Αναθέτουμε στην εταιρεία",
        "Κατακυρώνεται",
    ),
}

CONTEXTUAL_ROLE_CUES = {
    "recipient": (
        "τελικό φορέα",
        "για τις ανάγκες",
        "ωφελούμενος φορέας",
    ),
    "contractor": (
        "διάθεση ποσού",
        "δικαιούχος πληρωμής",
    ),
}


def _find_phrase_anchors(
    phrase: str,
    source_text: str,
    context_chars: int,
    max_matches: int,
) -> list[dict]:
    """Find case-insensitive phrases while preserving offsets."""

    tokens = phrase.split()

    if not tokens or not source_text:
        return []

    pattern = (
        r"(?<!\w)"
        + r"\s+".join(re.escape(token) for token in tokens)
        + r"(?!\w)"
    )

    anchors = []

    for match in re.finditer(
        pattern,
        source_text,
        flags=re.IGNORECASE,
    ):
        start, end = match.span()

        context_start = max(0, start - context_chars)
        context_end = min(
            len(source_text),
            end + context_chars,
        )

        anchors.append({
            "text": source_text[start:end],
            "start": start,
            "end": end,
            "context": source_text[context_start:context_end],
            "context_start": context_start,
            "context_end": context_end,
        })

        if len(anchors) >= max_matches:
            break

    return anchors


def select_document_evidence(
    value: str,
    page_texts: dict[int, str],
    *,
    context_chars: int = 250,
    max_total_matches: int = 5,
) -> list[dict]:
    """Retrieve page-aware entity evidence with original offsets."""

    if max_total_matches < 1:
        raise ValueError("max_total_matches must be positive")

    if not value or not value.strip():
        return []

    anchors = []

    for page_number, text in sorted(page_texts.items()):
        matches = find_text_anchors(
            value=value,
            source_text=text,
            context_chars=context_chars,
            max_matches=max_total_matches,
        )

        for match in matches:
            anchors.append({
                **match,
                "page_number": page_number,
                "evidence_type": "entity_value",
                "role_cue": None,
            })

            if len(anchors) >= max_total_matches:
                return anchors

    return anchors


def select_role_evidence(
    field_name: str,
    value: str,
    page_texts: dict[int, str],
    *,
    context_chars: int = 250,
    max_total_matches: int = 10,
) -> list[dict]:
    """Retrieve entity, explicit role and contextual evidence."""

    if max_total_matches < 1:
        raise ValueError("max_total_matches must be positive")

    if not value or not value.strip():
        return []

    if field_name not in ROLE_CUES:
        raise ValueError(f"Unsupported role field: {field_name}")

    selected = []
    seen = set()

    for page_number, text in sorted(page_texts.items()):

        evidence_groups = (
            (
                "entity_value",
                (value,),
            ),
            (
                "role_cue",
                ROLE_CUES[field_name],
            ),
            (
                "contextual_role",
                CONTEXTUAL_ROLE_CUES.get(field_name, ()),
            ),
        )

        for evidence_type, phrases in evidence_groups:
            for phrase in phrases:
                matches = _find_phrase_anchors(
                    phrase=phrase,
                    source_text=text,
                    context_chars=context_chars,
                    max_matches=max_total_matches,
                )

                for match in matches:
                    key = (
                        page_number,
                        match["start"],
                        match["end"],
                    )

                    if key in seen:
                        continue

                    seen.add(key)

                    selected.append({
                        **match,
                        "page_number": page_number,
                        "evidence_type": evidence_type,
                        "role_cue": (
                            phrase if evidence_type != "entity_value"
                            else None
                        ),
                    })

                    if len(selected) >= max_total_matches:
                        return selected

    return selected
