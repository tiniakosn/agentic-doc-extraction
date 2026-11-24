
def _matches_gold(candidate: dict, gold: dict) -> bool:
    """Check whether a retrieved span belongs to a gold span."""

    return (
        candidate["page_number"] == gold["page_number"]
        and candidate["evidence_type"] == gold["evidence_type"]
        and gold["start"] <= candidate["start"]
        and candidate["end"] <= gold["end"]
    )


def evaluate_evidence(
    candidates: list[dict],
    gold_evidence: list[dict],
) -> dict:
    """Calculate evidence precision, recall and page coverage."""

    matched_candidates = set()
    matched_gold = set()

    for candidate_index, candidate in enumerate(candidates):
        for gold_index, gold in enumerate(gold_evidence):
            if _matches_gold(candidate, gold):
                matched_candidates.add(candidate_index)
                matched_gold.add(gold_index)

    candidate_count = len(candidates)
    gold_count = len(gold_evidence)

    precision = (
        len(matched_candidates) / candidate_count
        if candidate_count else 0.0
    )

    recall = (
        len(matched_gold) / gold_count
        if gold_count else 0.0
    )

    gold_pages = {
        item["page_number"]
        for item in gold_evidence
    }

    matched_pages = {
        candidates[index]["page_number"]
        for index in matched_candidates
    }

    page_coverage = (
        len(gold_pages & matched_pages) / len(gold_pages)
        if gold_pages else 0.0
    )

    return {
        "candidate_count": candidate_count,
        "gold_count": gold_count,
        "matched_candidates": len(matched_candidates),
        "matched_gold": len(matched_gold),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "page_coverage": round(page_coverage, 4),
        "pages_represented": sorted(matched_pages),
        "gold_pages": sorted(gold_pages),
    }


def calculate_deduplication_rate(
    raw_count: int,
    deduplicated_count: int,
) -> float:
    """Calculate the proportion of candidates removed."""

    if raw_count == 0:
        return 0.0

    return round(
        (raw_count - deduplicated_count) / raw_count,
        4,
    )


def calculate_budget_utilization(
    estimated_tokens: int,
    token_budget: int,
) -> float:
    if token_budget <= 0:
        raise ValueError("token_budget must be positive")

    return round(
        estimated_tokens / token_budget,
        4,
    )


GOLD_TO_CANDIDATE_TYPES = {
    "entity_value": {"entity_value"},
    "role_cue": {"role_cue"},
    "distractor_role_cue": {"role_cue"},
    "negative_role_context": {"role_cue"},
    "contextual_role": {"contextual_role"},
}


def _candidate_matches_gold(candidate, gold):
    allowed_types = GOLD_TO_CANDIDATE_TYPES.get(
        gold["evidence_type"],
        set(),
    )

    return (
        candidate["page_number"] == gold["page_number"]
        and candidate["evidence_type"] in allowed_types
        and candidate["start"] < gold["end"]
        and candidate["end"] > gold["start"]
    )


def match_candidates_one_to_one(candidates, gold_evidence):
    """Maximum one-to-one matching between retrieved and gold spans."""

    candidate_to_gold = {}

    def augment(gold_index, visited):
        gold = gold_evidence[gold_index]

        for candidate_index, candidate in enumerate(candidates):
            if candidate_index in visited:
                continue

            if not _candidate_matches_gold(candidate, gold):
                continue

            visited.add(candidate_index)

            previous_gold = candidate_to_gold.get(candidate_index)

            if (
                previous_gold is None
                or augment(previous_gold, visited)
            ):
                candidate_to_gold[candidate_index] = gold_index
                return True

        return False

    for gold_index in range(len(gold_evidence)):
        augment(gold_index, set())

    return {
        "matched_candidates": set(candidate_to_gold),
        "matched_gold": set(candidate_to_gold.values()),
    }


def evaluate_evidence_one_to_one(candidates, gold_evidence):
    """Calculate metrics without counting gold spans more than once."""

    matches = match_candidates_one_to_one(
        candidates,
        gold_evidence,
    )

    matched_candidates = len(matches["matched_candidates"])
    matched_gold = len(matches["matched_gold"])

    precision = (
        matched_candidates / len(candidates)
        if candidates else 0.0
    )

    recall = (
        matched_gold / len(gold_evidence)
        if gold_evidence else 0.0
    )

    gold_pages = {
        item["page_number"]
        for item in gold_evidence
    }

    matched_pages = {
        candidates[index]["page_number"]
        for index in matches["matched_candidates"]
    }

    page_coverage = (
        len(gold_pages & matched_pages) / len(gold_pages)
        if gold_pages else 0.0
    )

    return {
        "candidate_count": len(candidates),
        "gold_count": len(gold_evidence),
        "matched_candidates": matched_candidates,
        "matched_gold": matched_gold,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "page_coverage": round(page_coverage, 4),
    }
