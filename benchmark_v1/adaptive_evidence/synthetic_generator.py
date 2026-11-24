
from dataclasses import dataclass, field


@dataclass
class SyntheticDocument:
    document_id: str
    page_count: int
    page_texts: dict[int, str]
    gold_evidence: list[dict] = field(default_factory=list)


def _add_evidence(
    document,
    page_number,
    text,
    evidence_type,
):
    page_text = document.page_texts[page_number]
    separator = "\n"

    start = len(page_text) + len(separator)
    end = start + len(text)

    document.page_texts[page_number] = (
        page_text + separator + text
    )

    document.gold_evidence.append({
        "page_number": page_number,
        "start": start,
        "end": end,
        "text": text,
        "evidence_type": evidence_type,
    })


def generate_synthetic_document(
    page_count: int,
) -> SyntheticDocument:
    """Generate a deterministic multi-page test document."""

    if page_count < 1:
        raise ValueError("page_count must be positive")

    document = SyntheticDocument(
        document_id=f"synthetic_{page_count}_pages",
        page_count=page_count,
        page_texts={
            page: (
                f"Διοικητικό έγγραφο {page}. "
                "Γενικές πληροφορίες και περιγραφικό κείμενο. "
            ) * 3
            for page in range(1, page_count + 1)
        },
    )

    target_pages = sorted({
        1,
        max(1, page_count // 2),
        page_count,
    })

    # Entity mentions: exact occurrences of the claimed entity.
    for page_number in target_pages:
        _add_evidence(
            document,
            page_number,
            "Η επιχείρηση ΑΛΦΑ αναφέρεται στο έγγραφο.",
            "entity_value",
        )

    # Known role cue supported by the current retrieval vocabulary.
    known_page = target_pages[-1]

    _add_evidence(
        document,
        known_page,
        "Αναθέτουμε στην επιχείρηση ΑΛΦΑ την προμήθεια εξοπλισμού.",
        "role_cue",
    )

    # Unseen role formulation: deliberately not in ROLE_CUES.
    unseen_page = target_pages[0]

    _add_evidence(
        document,
        unseen_page,
        "Η προμήθεια θα εκτελεστεί από την εταιρεία ΑΛΦΑ.",
        "role_cue",
    )

    return document


def generate_synthetic_suite(
    page_counts=(2, 10, 25, 50),
) -> list[SyntheticDocument]:
    """Generate documents with different page counts."""

    return [
        generate_synthetic_document(page_count)
        for page_count in page_counts
    ]
