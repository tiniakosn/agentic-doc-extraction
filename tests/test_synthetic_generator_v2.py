
from benchmark_v1.adaptive_evidence.synthetic_generator_v2 import (
    TARGET_ENTITY,
    DISTRACTOR_ENTITY,
    generate_synthetic_suite_v2,
)


def test_generates_expected_document_sizes():
    documents = generate_synthetic_suite_v2()

    assert [
        document.page_count
        for document in documents
    ] == [2, 10, 25, 50]


def test_ground_truth_offsets_are_valid():
    for document in generate_synthetic_suite_v2():
        for item in document.gold_evidence:
            page_text = document.page_texts[item["page_number"]]

            assert (
                page_text[item["start"]:item["end"]]
                == item["text"]
            )


def test_contains_known_and_unseen_role_formulations():
    for document in generate_synthetic_suite_v2():
        evidence_types = {
            item["evidence_type"]
            for item in document.gold_evidence
        }

        assert "role_cue" in evidence_types
        assert "unseen_role_formulation" in evidence_types


def test_contains_distractors_and_ambiguous_context():
    for document in generate_synthetic_suite_v2():
        metadata = document.scenario_metadata

        assert metadata["distractor_role_formulations"] == 1
        assert metadata["contextual_role_formulations"] == 1
        assert metadata["negative_role_formulations"] == 1


def test_entities_are_distinct():
    assert TARGET_ENTITY != DISTRACTOR_ENTITY

    for document in generate_synthetic_suite_v2():
        assert document.target_entity == TARGET_ENTITY


def test_repeated_mentions_increase_with_document_complexity():
    documents = generate_synthetic_suite_v2()

    for document in documents:
        occurrences = sum(
            page_text.count(TARGET_ENTITY)
            for page_text in document.page_texts.values()
        )

        assert occurrences >= document.scenario_metadata[
            "repeated_entity_mentions"
        ]
