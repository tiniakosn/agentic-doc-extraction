from benchmark_v1.adaptive_evidence.synthetic_generator import (
    generate_synthetic_suite,
)


def test_generates_documents_with_expected_page_counts():
    documents = generate_synthetic_suite()

    assert [
        document.page_count
        for document in documents
    ] == [2, 10, 25, 50]


def test_ground_truth_preserves_original_offsets():
    documents = generate_synthetic_suite()

    for document in documents:
        for evidence in document.gold_evidence:
            page_text = document.page_texts[
                evidence["page_number"]
            ]

            assert (
                page_text[
                    evidence["start"]:evidence["end"]
                ] == evidence["text"]
            )


def test_dataset_contains_known_and_unseen_role_formulations():
    documents = generate_synthetic_suite()

    for document in documents:
        role_evidence = [
            item
            for item in document.gold_evidence
            if item["evidence_type"] == "role_cue"
        ]

        assert len(role_evidence) == 2