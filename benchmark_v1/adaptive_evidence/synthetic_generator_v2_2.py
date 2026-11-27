
from dataclasses import dataclass, field


TARGET_ENTITY = "ΑΛΦΑ ΤΕΧΝΙΚΗ Α.Ε."
DISTRACTOR_ENTITY = "ΒΗΤΑ ΕΜΠΟΡΙΚΗ Α.Ε."


@dataclass
class SyntheticDocumentV22:
    document_id: str
    page_count: int
    target_entity: str
    page_texts: dict[int, str]
    annotations: list[dict] = field(default_factory=list)
    scenario_metadata: dict = field(default_factory=dict)


def _append_sentence(
    document: SyntheticDocumentV22,
    page_number: int,
    sentence: str,
    *,
    entity: str | None = None,
    role: str | None = None,
    role_cue: str | None = None,
    annotation_type: str,
    polarity: str | None = None,
    supports_claim: bool = False,
    formulation_type: str = "not_applicable",
):
    """Append a sentence and preserve exact character provenance."""

    if not 1 <= page_number <= document.page_count:
        raise ValueError("Invalid page number")

    if entity is not None and entity not in sentence:
        raise ValueError("Entity not found in sentence")

    if role_cue is not None and role_cue not in sentence:
        raise ValueError("Role cue not found in sentence")

    current_text = document.page_texts[page_number]
    separator = "\n" if current_text else ""

    sentence_start = len(current_text) + len(separator)
    sentence_end = sentence_start + len(sentence)

    document.page_texts[page_number] = (
        current_text + separator + sentence
    )

    annotation = {
        "annotation_type": annotation_type,
        "page_number": page_number,
        "sentence_start": sentence_start,
        "sentence_end": sentence_end,
        "sentence": sentence,
        "entity": entity,
        "role": role,
        "polarity": polarity,
        "supports_claim": supports_claim,
        "formulation_type": formulation_type,
    }

    if entity is not None:
        entity_start = sentence.index(entity)

        annotation.update({
            "entity_start": sentence_start + entity_start,
            "entity_end": sentence_start + entity_start + len(entity),
        })

    if role_cue is not None:
        cue_start = sentence.index(role_cue)

        annotation.update({
            "role_cue": role_cue,
            "role_cue_start": sentence_start + cue_start,
            "role_cue_end": sentence_start + cue_start + len(role_cue),
        })

    document.annotations.append(annotation)


def _spread_pages(page_count: int) -> list[int]:
    """Choose three page assignments across the document."""

    if page_count < 2:
        raise ValueError("page_count must be at least 2")

    fractions = (0.15, 0.50, 0.85)

    pages = [
        max(1, min(page_count, round(page_count * fraction)))
        for fraction in fractions
    ]

    return pages


def generate_synthetic_document_v2_2(
    page_count: int,
) -> SyntheticDocumentV22:
    """Generate a document with relation-level ground truth."""

    if page_count < 2:
        raise ValueError("page_count must be at least 2")

    pages = _spread_pages(page_count)

    document = SyntheticDocumentV22(
        document_id=f"synthetic_v2_2_{page_count}_pages",
        page_count=page_count,
        target_entity=TARGET_ENTITY,
        page_texts={
            page: (
                f"Διοικητικό έγγραφο σελίδας {page}.\n"
                "Γενικές πληροφορίες, διοικητικές πράξεις, "
                "περιγραφή διαδικασίας και οικονομικά στοιχεία."
            )
            for page in range(1, page_count + 1)
        },
        scenario_metadata={
            "dataset_version": "v2.2",
            "page_count": page_count,
            "target_entity": TARGET_ENTITY,
            "distractor_entity": DISTRACTOR_ENTITY,
        },
    )

    known_page, second_known_page, unseen_page = pages

    
    # 1. Repeated entity mentions without an established role.
    repeated_mentions = min(8, page_count)

    for _ in range(repeated_mentions):
        _append_sentence(
            document,
            1,
            f"Η επιχείρηση {TARGET_ENTITY} αναφέρεται "
            "στα συνοδευτικά στοιχεία.",
            entity=TARGET_ENTITY,
            role=None,
            annotation_type="entity_mention",
            polarity=None,
            supports_claim=False,
            formulation_type="not_applicable",
        )

    # 2. Explicit contractor award.
    _append_sentence(
        document,
        known_page,
        f"Αναθέτουμε στην επιχείρηση {TARGET_ENTITY} "
        "την προμήθεια και εγκατάσταση εξοπλισμού.",
        entity=TARGET_ENTITY,
        role="contractor",
        role_cue="Αναθέτουμε στην επιχείρηση",
        annotation_type="role_relation",
        polarity="positive",
        supports_claim=True,
        formulation_type="known",
    )

    # 3. Alternative known award formulation.
    _append_sentence(
        document,
        second_known_page,
        f"Κατακυρώνεται στην εταιρεία {TARGET_ENTITY} "
        "η προμήθεια των υλικών.",
        entity=TARGET_ENTITY,
        role="contractor",
        role_cue="Κατακυρώνεται",
        annotation_type="role_relation",
        polarity="positive",
        supports_claim=True,
        formulation_type="known",
    )

    # 4. Unseen but semantically valid role formulation.
    _append_sentence(
        document,
        unseen_page,
        f"Η προμήθεια θα εκτελεστεί από την εταιρεία "
        f"{TARGET_ENTITY}.",
        entity=TARGET_ENTITY,
        role="contractor",
        annotation_type="role_relation",
        polarity="positive",
        supports_claim=True,
        formulation_type="unseen",
    )

    # 5. Different organization awarded a different contract.
    distractor_page = max(
        1,
        min(page_count, round(page_count * 0.30)),
    )

    _append_sentence(
        document,
        distractor_page,
        f"Αναθέτουμε στην επιχείρηση {DISTRACTOR_ENTITY} "
        "διαφορετική προμήθεια.",
        entity=DISTRACTOR_ENTITY,
        role="contractor",
        role_cue="Αναθέτουμε στην επιχείρηση",
        annotation_type="role_relation",
        polarity="positive",
        supports_claim=False,
        formulation_type="known",
    )

    # 6. Explicit negative relation.
    negative_page = max(
        1,
        min(page_count, round(page_count * 0.70)),
    )

    _append_sentence(
        document,
        negative_page,
        f"Δεν κατακυρώνεται στην επιχείρηση "
        f"{TARGET_ENTITY} η συγκεκριμένη προμήθεια.",
        entity=TARGET_ENTITY,
        role="contractor",
        role_cue="κατακυρώνεται",
        annotation_type="role_relation",
        polarity="negative",
        supports_claim=False,
        formulation_type="known",
    )

    # 7. Contextual mention without a concluded award.
    _append_sentence(
        document,
        page_count,
        f"Η εταιρεία {TARGET_ENTITY} αναφέρεται "
        "ως δικαιούχος πληρωμής.",
        entity=TARGET_ENTITY,
        role="payment_beneficiary",
        role_cue="δικαιούχος πληρωμής",
        annotation_type="role_relation",
        polarity="ambiguous",
        supports_claim=False,
        formulation_type="contextual",
    )


    document.scenario_metadata.update({
        "repeated_entity_mentions": repeated_mentions,
        "positive_role_relations": 3,
        "distractor_relations": 1,
        "negative_relations": 1,
        "ambiguous_relations": 1,
        "positive_evidence_pages": pages,
    })

    return document


def generate_synthetic_suite_v2_2(
    page_counts=(2, 10, 25, 50),
) -> list[SyntheticDocumentV22]:
    """Generate the v2.2 synthetic evaluation suite."""

    return [
        generate_synthetic_document_v2_2(page_count)
        for page_count in page_counts
    ]
