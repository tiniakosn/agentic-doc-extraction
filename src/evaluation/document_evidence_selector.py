
from src.evaluation.text_evidence_anchor import find_text_anchors


def select_document_evidence(
    value: str,
    page_texts: dict[int, str],
    *,
    context_chars: int = 250,
    max_total_matches: int = 5,
) -> list[dict]:
    """Retrieve page-aware text evidence with original offsets."""

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
            })

            if len(anchors) >= max_total_matches:
                return anchors

    return anchors
