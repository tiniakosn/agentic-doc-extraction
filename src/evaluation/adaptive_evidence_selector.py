
import json
import re
from collections import defaultdict
from typing import Callable, Any

from src.evaluation.document_evidence_selector import (
    select_role_evidence,
)


EVIDENCE_WEIGHTS = {
    "role_cue": 3.0,
    "contextual_role": 2.0,
    "entity_value": 1.0,
}


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).casefold().strip()


def retrieve_candidates(
    field_name: str,
    value: str,
    page_texts: dict[int, str],
    *,
    context_chars: int = 250,
    max_candidates_per_page: int = 20,
) -> list[dict]:
    """Retrieve candidates independently from every page."""

    if max_candidates_per_page < 1:
        raise ValueError(
            "max_candidates_per_page must be positive"
        )

    candidates = []

    for page_number, text in sorted(page_texts.items()):
        page_candidates = select_role_evidence(
            field_name=field_name,
            value=value,
            page_texts={page_number: text},
            context_chars=context_chars,
            max_total_matches=max_candidates_per_page * 3,
            max_matches_per_type=max_candidates_per_page,
        )

        candidates.extend(page_candidates)

    return candidates


def deduplicate_candidates(
    candidates: list[dict],
) -> list[dict]:
    """Remove duplicate and nested matches on the same page.

    Different evidence types are preserved because they represent
    different semantic roles.
    """

    ordered = sorted(
        candidates,
        key=lambda item: (
            item["page_number"],
            item["evidence_type"],
            -(item["end"] - item["start"]),
            item["start"],
        ),
    )

    selected = []

    for candidate in ordered:
        duplicate = False

        for existing in selected:
            if (
                existing["page_number"]
                != candidate["page_number"]
                or existing["evidence_type"]
                != candidate["evidence_type"]
            ):
                continue

            overlaps = (
                candidate["start"] < existing["end"]
                and candidate["end"] > existing["start"]
            )

            if overlaps:
                duplicate = True
                break

        if not duplicate:
            selected.append(candidate)

    return selected


def rank_candidates(
    candidates: list[dict],
    claimed_value: str,
) -> list[dict]:
    """Apply deterministic, document-independent relevance ranking."""

    normalized_value = _normalize_text(claimed_value)

    ranked = []

    for candidate in candidates:
        evidence_type = candidate["evidence_type"]

        score = EVIDENCE_WEIGHTS.get(evidence_type, 0.0)

        normalized_context = _normalize_text(
            candidate["context"]
        )

        # A role cue is more informative when the claimed
        # entity also occurs in the same context.
        if (
            evidence_type != "entity_value"
            and normalized_value
            and normalized_value in normalized_context
        ):
            score += 1.0

        ranked.append({
            **candidate,
            "relevance_score": score,
        })

    return sorted(
        ranked,
        key=lambda item: (
            -item["relevance_score"],
            item["page_number"],
            item["start"],
        ),
    )


def _estimate_selection_tokens(
    candidates: list[dict],
    token_counter: Callable[[str], int],
) -> int:
    """Estimate tokens of the serialized evidence payload."""

    serialized = json.dumps(
        candidates,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return token_counter(serialized)


def select_with_budget(
    candidates: list[dict],
    *,
    token_budget: int,
    token_counter: Callable[[str], int],
    max_selected: int = 10,
    max_per_page: int = 3,
) -> dict[str, Any]:
    """Select ranked evidence with page coverage and token limits."""

    if token_budget < 1:
        raise ValueError("token_budget must be positive")

    if max_selected < 1 or max_per_page < 1:
        raise ValueError("Selection limits must be positive")

    if not callable(token_counter):
        raise TypeError("token_counter must be callable")

    ranked = sorted(
        candidates,
        key=lambda item: (
            -item["relevance_score"],
            item["page_number"],
            item["start"],
        ),
    )

    by_page = defaultdict(list)

    for candidate in ranked:
        by_page[candidate["page_number"]].append(candidate)

    selected = []
    selected_ids = set()
    attempted_ids = set()
    page_counts = defaultdict(int)
    skipped_over_budget = 0

    def try_select(candidate):
        nonlocal skipped_over_budget

        key = (
            candidate["page_number"],
            candidate["start"],
            candidate["end"],
            candidate["evidence_type"],
        )

        # Do not retry a candidate already selected or evaluated.
        if key in selected_ids or key in attempted_ids:
            return False

        if page_counts[candidate["page_number"]] >= max_per_page:
            return False

        if len(selected) >= max_selected:
            return False

        attempted_ids.add(key)

        proposed = [*selected, candidate]

        estimated = _estimate_selection_tokens(
            proposed,
            token_counter,
        )

        if estimated > token_budget:
            skipped_over_budget += 1
            return False

        selected.append(candidate)
        selected_ids.add(key)
        page_counts[candidate["page_number"]] += 1

        return True

    # First pass: select the strongest candidate from each page.
    page_order = sorted(
        by_page,
        key=lambda page: (
            -by_page[page][0]["relevance_score"],
            page,
        ),
    )

    for page_number in page_order:
        if len(selected) >= max_selected:
            break

        try_select(by_page[page_number][0])

    # Second pass: fill remaining budget using global ranking.
    for candidate in ranked:
        if len(selected) >= max_selected:
            break

        try_select(candidate)

    estimated_tokens = (
        _estimate_selection_tokens(selected, token_counter)
        if selected
        else 0
    )

    selected_pages = sorted(page_counts)

    candidate_pages = sorted(by_page)

    return {
        "selected_evidence": selected,
        "candidates": ranked,
        "total_candidates": len(candidates),
        "selected_count": len(selected),
        "estimated_tokens": estimated_tokens,
        "page_coverage": selected_pages,
        "selection_metadata": {
            "deduplicated_count": len(candidates),
            "budget_limit": token_budget,
            "budget_exceeded": estimated_tokens > token_budget,
            "candidate_pages": candidate_pages,
            "uncovered_pages": sorted(
                set(candidate_pages) - set(selected_pages)
            ),
            "per_page_selected_counts": dict(page_counts),
            "skipped_over_budget": skipped_over_budget,
        },
    }


def select_adaptive_evidence(
    field_name: str,
    value: str,
    page_texts: dict[int, str],
    *,
    token_budget: int,
    token_counter: Callable[[str], int],
    context_chars: int = 250,
    max_candidates_per_page: int = 20,
    max_selected: int = 10,
    max_per_page: int = 3,
) -> dict[str, Any]:
    """Complete adaptive retrieval, ranking and selection pipeline."""

    raw_candidates = retrieve_candidates(
        field_name=field_name,
        value=value,
        page_texts=page_texts,
        context_chars=context_chars,
        max_candidates_per_page=max_candidates_per_page,
    )

    deduplicated = deduplicate_candidates(raw_candidates)

    ranked = rank_candidates(
        deduplicated,
        claimed_value=value,
    )

    result = select_with_budget(
        ranked,
        token_budget=token_budget,
        token_counter=token_counter,
        max_selected=max_selected,
        max_per_page=max_per_page,
    )

    result["raw_candidate_count"] = len(raw_candidates)
    result["selection_metadata"]["raw_candidate_count"] = (
        len(raw_candidates)
    )

    return result
