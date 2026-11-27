
def _context_exposes_relation(
    candidate: dict,
    annotation: dict,
) -> bool:
    """Check whether a candidate context contains the full relation."""

    return (
        candidate["page_number"] == annotation["page_number"]
        and candidate["context_start"] <= annotation["sentence_start"]
        and candidate["context_end"] >= annotation["sentence_end"]
    )


def _directly_retrieves_role_cue(
    candidate: dict,
    annotation: dict,
) -> bool:
    """Check whether the candidate directly retrieves an annotated cue."""

    if "role_cue_start" not in annotation:
        return False

    return (
        candidate["page_number"] == annotation["page_number"]
        and candidate["evidence_type"] == "role_cue"
        and candidate["start"] <= annotation["role_cue_start"]
        and candidate["end"] >= annotation["role_cue_end"]
    )


def _maximum_one_to_one_match(
    candidates: list[dict],
    annotations: list[dict],
    matcher,
) -> set[int]:
    """Return matched annotation indices using one-to-one matching."""

    candidate_to_annotation = {}

    def augment(annotation_index, visited):
        annotation = annotations[annotation_index]

        for candidate_index, candidate in enumerate(candidates):
            if candidate_index in visited:
                continue

            if not matcher(candidate, annotation):
                continue

            visited.add(candidate_index)

            previous = candidate_to_annotation.get(candidate_index)

            if (
                previous is None
                or augment(previous, visited)
            ):
                candidate_to_annotation[candidate_index] = (
                    annotation_index
                )
                return True

        return False

    for annotation_index in range(len(annotations)):
        augment(annotation_index, set())

    return set(candidate_to_annotation.values())


def evaluate_relations(
    candidates: list[dict],
    annotations: list[dict],
) -> dict:
    """Evaluate relation exposure and direct role-cue retrieval."""

    relations = [
        item for item in annotations
        if item["annotation_type"] == "role_relation"
    ]

    supporting = [
        item for item in relations
        if item["supports_claim"]
    ]

    non_supporting = [
        item for item in relations
        if not item["supports_claim"]
    ]

    unseen = [
        item for item in supporting
        if item["formulation_type"] == "unseen"
    ]

    known = [
        item for item in relations
        if item["formulation_type"] == "known"
    ]

    exposed = _maximum_one_to_one_match(
        candidates,
        relations,
        _context_exposes_relation,
    )

    supporting_exposed = _maximum_one_to_one_match(
        candidates,
        supporting,
        _context_exposes_relation,
    )

    non_supporting_exposed = _maximum_one_to_one_match(
        candidates,
        non_supporting,
        _context_exposes_relation,
    )

    known_direct = _maximum_one_to_one_match(
        candidates,
        known,
        _directly_retrieves_role_cue,
    )

    unseen_exposed = _maximum_one_to_one_match(
        candidates,
        unseen,
        _context_exposes_relation,
    )

    def rate(matched, total):
        return round(len(matched) / len(total), 4) if total else 0.0

    return {
        "relation_count": len(relations),
        "supporting_relation_count": len(supporting),
        "non_supporting_relation_count": len(non_supporting),

        "relation_context_exposure": rate(
            exposed, relations
        ),

        "supporting_relation_recall": rate(
            supporting_exposed, supporting
        ),

        "non_supporting_relation_exposure": rate(
            non_supporting_exposed, non_supporting
        ),

        "known_direct_role_cue_recall": rate(
            known_direct, known
        ),

        "unseen_relation_context_exposure": rate(
            unseen_exposed, unseen
        ),

        "matched_relations": sorted(exposed),
    }
