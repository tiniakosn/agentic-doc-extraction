
from benchmark_v1.adaptive_evidence.synthetic_generator_v2_2 import (
    TARGET_ENTITY,
    generate_synthetic_suite_v2_2,
)


def test_generates_expected_document_sizes():
    documents = generate_synthetic_suite_v2_2()

    assert [
        document.page_count for document in documents
    ] == [2, 10, 25, 50]


def test_all_annotation_offsets_are_valid():
    for document in generate_synthetic_suite_v2_2():
        for annotation in document.annotations:
            text = document.page_texts[
                annotation["page_number"]
            ]

            assert (
                text[
                    annotation["sentence_start"]:
                    annotation["sentence_end"]
                ] == annotation["sentence"]
            )

            if annotation.get("entity") is not None:
                assert (
                    text[
                        annotation["entity_start"]:
                        annotation["entity_end"]
                    ] == annotation["entity"]
                )

            if annotation.get("role_cue") is not None:
                assert (
                    text[
                        annotation["role_cue_start"]:
                        annotation["role_cue_end"]
                    ] == annotation["role_cue"]
                )


def test_distinguishes_entity_mentions_from_role_relations():
    for document in generate_synthetic_suite_v2_2():
        mentions = [
            item for item in document.annotations
            if item["annotation_type"] == "entity_mention"
        ]

        relations = [
            item for item in document.annotations
            if item["annotation_type"] == "role_relation"
        ]

        assert mentions
        assert relations

        assert all(
            item["role"] is None
            for item in mentions
        )


def test_positive_relations_have_explicit_support():
    for document in generate_synthetic_suite_v2_2():
        positive = [
            item for item in document.annotations
            if item["polarity"] == "positive"
            and item["entity"] == TARGET_ENTITY
        ]

        assert len(positive) == 3
        assert all(
            item["supports_claim"] is True
            for item in positive
        )


def test_distractor_negative_and_ambiguous_relations():
    for document in generate_synthetic_suite_v2_2():
        relations = [
            item for item in document.annotations
            if item["annotation_type"] == "role_relation"
        ]

        distractors = [
            item for item in relations
            if item["entity"] != TARGET_ENTITY
        ]

        negatives = [
            item for item in relations
            if item["polarity"] == "negative"
        ]

        ambiguous = [
            item for item in relations
            if item["polarity"] == "ambiguous"
        ]

        assert len(distractors) == 1
        assert len(negatives) == 1
        assert len(ambiguous) == 1

        assert not any(
            item["supports_claim"]
            for item in distractors + negatives + ambiguous
        )


def test_positive_evidence_is_distributed_across_pages():
    for document in generate_synthetic_suite_v2_2():
        positive_pages = {
            item["page_number"]
            for item in document.annotations
            if item["polarity"] == "positive"
            and item["entity"] == TARGET_ENTITY
        }

        assert len(positive_pages) >= 2


def test_rejects_single_page_documents():
    import pytest

    from benchmark_v1.adaptive_evidence.synthetic_generator_v2_2 import (
        generate_synthetic_document_v2_2,
    )

    with pytest.raises(ValueError):
        generate_synthetic_document_v2_2(1)

def test_unseen_positive_relation_preserves_contractor_role():
    for document in generate_synthetic_suite_v2_2():
        unseen = [
            item for item in document.annotations
            if item.get("formulation_type") == "unseen"
        ]

        assert len(unseen) == 1

        assert unseen[0]["role"] == "contractor"
        assert unseen[0]["polarity"] == "positive"
        assert unseen[0]["supports_claim"] is True
        assert "role_cue" not in unseen[0]