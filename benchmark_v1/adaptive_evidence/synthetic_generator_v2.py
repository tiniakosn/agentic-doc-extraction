
from dataclasses import dataclass, field


TARGET_ENTITY = "ΑΛΦΑ ΤΕΧΝΙΚΗ Α.Ε."
DISTRACTOR_ENTITY = "ΒΗΤΑ ΕΜΠΟΡΙΚΗ Α.Ε."


@dataclass
class SyntheticDocumentV2:
    document_id: str
    page_count: int
    target_entity: str
    page_texts: dict[int, str]
    gold_evidence: list[dict] = field(default_factory=list)
    scenario_metadata: dict = field(default_factory=dict)


def append_text(
    document: SyntheticDocumentV2,
    page_number: int,
    text: str,
    evidence_type: str | None = None,
):
    """Append text and optionally record exact ground-truth offsets."""

    if not 1 <= page_number <= document.page_count:
        raise ValueError("Invalid page number")

    current_text = document.page_texts[page_number]

    separator = "\n" if current_text else ""
    start = len(current_text) + len(separator)
    end = start + len(text)

    document.page_texts[page_number] = (
        current_text + separator + text
    )

    if evidence_type is not None:
        document.gold_evidence.append({
            "page_number": page_number,
            "start": start,
            "end": end,
            "text": text,
            "evidence_type": evidence_type,
        })


def append_entity_mention(
    document: SyntheticDocumentV2,
    page_number: int,
    prefix: str = "Η επιχείρηση",
):
    """Add a target entity mention with exact offsets."""

    current_length = len(document.page_texts[page_number])

    separator = "\n" if current_length else ""
    sentence = f"{prefix} {document.target_entity} αναφέρεται."

    start = current_length + len(separator) + len(prefix) + 1
    end = start + len(document.target_entity)

    append_text(
        document,
        page_number,
        sentence,
    )

    document.gold_evidence.append({
        "page_number": page_number,
        "start": start,
        "end": end,
        "text": document.target_entity,
        "evidence_type": "entity_value",
    })


def append_role_evidence(
    document: SyntheticDocumentV2,
    page_number: int,
    sentence: str,
    matched_phrase: str,
    evidence_type: str,
):
    """Add a role-related sentence with exact annotated span."""

    current_length = len(document.page_texts[page_number])
    separator = "\n" if current_length else ""

    relative_start = sentence.index(matched_phrase)

    start = current_length + len(separator) + relative_start
    end = start + len(matched_phrase)

    append_text(
        document,
        page_number,
        sentence,
    )

    document.gold_evidence.append({
        "page_number": page_number,
        "start": start,
        "end": end,
        "text": matched_phrase,
        "evidence_type": evidence_type,
    })


def generate_synthetic_document_v2(
    page_count: int,
) -> SyntheticDocumentV2:
    """Generate a deterministic, heterogeneous synthetic document."""

    if page_count < 2:
        raise ValueError("page_count must be at least 2")

    document = SyntheticDocumentV2(
        document_id=f"synthetic_v2_{page_count}_pages",
        page_count=page_count,
        target_entity=TARGET_ENTITY,
        page_texts={
            page: (
                f"Διοικητικό έγγραφο σελίδας {page}.\n"
                "Γενικές πληροφορίες, περιγραφή διαδικασίας, "
                "διοικητικές αναφορές και στοιχεία προϋπολογισμού."
            )
            for page in range(1, page_count + 1)
        },
        scenario_metadata={
            "dataset_version": "v2",
            "page_count": page_count,
            "target_entity": TARGET_ENTITY,
            "distractor_entity": DISTRACTOR_ENTITY,
        },
    )

    first_page = 1
    middle_page = max(2, page_count // 2)
    last_page = page_count

    # 1. Repeated target entity mentions.
    # This tests whether frequent entity mentions suppress other evidence.
    repeated_mentions = min(8, page_count)

    for _ in range(repeated_mentions):
        append_entity_mention(
            document,
            first_page,
        )

    # 2. Entity mentions distributed across the document.
    append_entity_mention(document, middle_page)
    append_entity_mention(document, last_page)

    # 3. Explicit, known contractor formulation.
    append_role_evidence(
        document,
        last_page,
        (
            f"Αναθέτουμε στην επιχείρηση "
            f"{TARGET_ENTITY} την προμήθεια εξοπλισμού."
        ),
        "Αναθέτουμε στην επιχείρηση",
        "role_cue",
    )

    # 4. Unseen but semantically relevant formulation.
    # This phrase is intentionally absent from ROLE_CUES.
    append_role_evidence(
        document,
        middle_page,
        (
            f"Η προμήθεια θα εκτελεστεί από την εταιρεία "
            f"{TARGET_ENTITY}."
        ),
        (
            f"Η προμήθεια θα εκτελεστεί από την εταιρεία "
            f"{TARGET_ENTITY}"
        ),
        "unseen_role_formulation",
    )

    # 5. Distractor: a different company receives an award.
    append_role_evidence(
        document,
        max(1, page_count // 3),
        (
            f"Αναθέτουμε στην επιχείρηση "
            f"{DISTRACTOR_ENTITY} διαφορετική προμήθεια."
        ),
        "Αναθέτουμε στην επιχείρηση",
        "distractor_role_cue",
    )

    # 6. Ambiguous reference: target mentioned in payment context.
    append_role_evidence(
        document,
        last_page,
        (
            f"Η εταιρεία {TARGET_ENTITY} αναφέρεται "
            "ως δικαιούχος πληρωμής."
        ),
        "δικαιούχος πληρωμής",
        "contextual_role",
    )

    # 7. Negative context: a role cue occurs under negation.
    append_role_evidence(
        document,
        middle_page,
        (
            f"Δεν κατακυρώνεται στην επιχείρηση "
            f"{TARGET_ENTITY} η συγκεκριμένη προμήθεια."
        ),
        "κατακυρώνεται",
        "negative_role_context",
    )

    document.scenario_metadata.update({
        "repeated_entity_mentions": repeated_mentions + 2,
        "known_role_formulations": 1,
        "unseen_role_formulations": 1,
        "distractor_role_formulations": 1,
        "contextual_role_formulations": 1,
        "negative_role_formulations": 1,
        "evidence_pages": sorted({
            item["page_number"]
            for item in document.gold_evidence
        }),
    })

    return document


def generate_synthetic_suite_v2(
    page_counts=(2, 10, 25, 50),
) -> list[SyntheticDocumentV2]:
    """Generate the complete v2 synthetic evaluation suite."""

    return [
        generate_synthetic_document_v2(page_count)
        for page_count in page_counts
    ]
