
from benchmark_v1.adaptive_evidence.metrics import (
    evaluate_evidence,
    calculate_deduplication_rate,
    calculate_budget_utilization,
)


def test_evidence_metrics_use_page_type_and_offsets():
    gold = [{
        "page_number": 2,
        "start": 100,
        "end": 150,
        "text": "Αναθέτουμε στην επιχείρηση ΑΛΦΑ",
        "evidence_type": "role_cue",
    }]

    candidates = [{
        "page_number": 2,
        "start": 100,
        "end": 125,
        "text": "Αναθέτουμε στην επιχείρηση",
        "evidence_type": "role_cue",
    }]

    result = evaluate_evidence(candidates, gold)

    assert result["precision"] == 1.0
    assert result["recall"] == 1.0
    assert result["page_coverage"] == 1.0


def test_wrong_page_does_not_match_gold():
    gold = [{
        "page_number": 2,
        "start": 100,
        "end": 150,
        "evidence_type": "role_cue",
    }]

    candidates = [{
        "page_number": 1,
        "start": 100,
        "end": 125,
        "evidence_type": "role_cue",
    }]

    result = evaluate_evidence(candidates, gold)

    assert result["precision"] == 0.0
    assert result["recall"] == 0.0


def test_wrong_evidence_type_does_not_match_gold():
    gold = [{
        "page_number": 1,
        "start": 10,
        "end": 30,
        "evidence_type": "role_cue",
    }]

    candidates = [{
        "page_number": 1,
        "start": 10,
        "end": 20,
        "evidence_type": "entity_value",
    }]

    result = evaluate_evidence(candidates, gold)

    assert result["recall"] == 0.0


def test_deduplication_rate():
    assert calculate_deduplication_rate(10, 8) == 0.2
    assert calculate_deduplication_rate(0, 0) == 0.0


def test_budget_utilization():
    assert calculate_budget_utilization(50, 100) == 0.5



from benchmark_v1.adaptive_evidence.metrics import (
    evaluate_evidence_one_to_one,
)


def test_duplicate_candidates_do_not_inflate_recall():
    gold = [{
        "page_number": 1,
        "start": 10,
        "end": 30,
        "evidence_type": "role_cue",
    }]

    candidates = [
        {
            "page_number": 1,
            "start": 10,
            "end": 30,
            "evidence_type": "role_cue",
        },
        {
            "page_number": 1,
            "start": 12,
            "end": 25,
            "evidence_type": "role_cue",
        },
    ]

    result = evaluate_evidence_one_to_one(
        candidates,
        gold,
    )

    assert result["matched_gold"] == 1
    assert result["matched_candidates"] == 1
    assert result["precision"] == 0.5
    assert result["recall"] == 1.0


def test_same_span_with_wrong_evidence_type_does_not_match():
    gold = [{
        "page_number": 1,
        "start": 10,
        "end": 30,
        "evidence_type": "role_cue",
    }]

    candidates = [{
        "page_number": 1,
        "start": 10,
        "end": 30,
        "evidence_type": "entity_value",
    }]

    result = evaluate_evidence_one_to_one(
        candidates,
        gold,
    )

    assert result["matched_gold"] == 0
    assert result["recall"] == 0.0


def test_one_candidate_cannot_match_two_gold_spans():
    candidates = [{
        "page_number": 1,
        "start": 10,
        "end": 40,
        "evidence_type": "role_cue",
    }]

    gold = [
        {
            "page_number": 1,
            "start": 10,
            "end": 25,
            "evidence_type": "role_cue",
        },
        {
            "page_number": 1,
            "start": 25,
            "end": 40,
            "evidence_type": "role_cue",
        },
    ]

    result = evaluate_evidence_one_to_one(
        candidates,
        gold,
    )

    assert result["matched_gold"] == 1
    assert result["recall"] == 0.5
