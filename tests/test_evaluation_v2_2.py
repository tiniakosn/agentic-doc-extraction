
from benchmark_v1.adaptive_evidence.evaluate_selector_v2_2 import (
    evaluate_document,
)

from benchmark_v1.adaptive_evidence.synthetic_generator_v2_2 import (
    generate_synthetic_document_v2_2,
)


def test_end_to_end_evaluation_returns_all_pipeline_stages():
    document = generate_synthetic_document_v2_2(10)

    result = evaluate_document(document)

    assert result["document_id"] == document.document_id

    assert set(result) >= {
        "raw_retrieval",
        "deduplicated_retrieval",
        "adaptive_selection",
        "deduplication",
        "selection",
    }

    for stage in (
        "raw_retrieval",
        "deduplicated_retrieval",
        "adaptive_selection",
    ):
        assert "entity_mentions" in result[stage]
        assert "relations" in result[stage]

    assert (
        result["deduplication"]["deduplicated_count"]
        <= result["deduplication"]["raw_count"]
    )

    assert result["selection"]["budget_exceeded"] is False


def test_end_to_end_evaluation_preserves_ground_truth_counts():
    document = generate_synthetic_document_v2_2(10)

    result = evaluate_document(document)

    assert result["gold_annotation_count"] == len(
        document.annotations
    )

    assert (
        result["raw_retrieval"]["relations"]["supporting_relation_count"]
        == 3
    )
