
from src.evaluation.adaptive_evidence_selector import (
    deduplicate_candidates,
)


def make_candidate(
    start,
    end,
    *,
    page=1,
    evidence_type="role_cue",
):
    return {
        "page_number": page,
        "start": start,
        "end": end,
        "evidence_type": evidence_type,
        "context": f"Evidence {start}-{end}",
    }


def test_removes_exact_duplicates():
    candidates = [
        make_candidate(10, 30),
        make_candidate(10, 30),
    ]

    result = deduplicate_candidates(candidates)

    assert len(result) == 1


def test_removes_nested_spans():
    candidates = [
        make_candidate(10, 50),
        make_candidate(20, 30),
    ]

    result = deduplicate_candidates(candidates)

    assert len(result) == 1
    assert result[0]["start"] == 10
    assert result[0]["end"] == 50


def test_removes_partially_overlapping_spans():
    candidates = [
        make_candidate(10, 30),
        make_candidate(25, 45),
    ]

    result = deduplicate_candidates(candidates)

    assert len(result) == 1


def test_preserves_adjacent_non_overlapping_spans():
    candidates = [
        make_candidate(10, 20),
        make_candidate(20, 30),
    ]

    result = deduplicate_candidates(candidates)

    assert len(result) == 2


def test_preserves_different_pages():
    candidates = [
        make_candidate(10, 30, page=1),
        make_candidate(10, 30, page=2),
    ]

    result = deduplicate_candidates(candidates)

    assert len(result) == 2


def test_preserves_different_evidence_types():
    candidates = [
        make_candidate(10, 30, evidence_type="role_cue"),
        make_candidate(10, 30, evidence_type="entity_value"),
    ]

    result = deduplicate_candidates(candidates)

    assert len(result) == 2


def test_preserves_multiple_independent_evidence_spans():
    candidates = [
        make_candidate(10, 30),
        make_candidate(40, 60),
        make_candidate(70, 90),
    ]

    result = deduplicate_candidates(candidates)

    assert len(result) == 3
