
import json
from unittest.mock import MagicMock, patch

from src.evaluation.claim_verifier import (
    ROLE_DEFINITIONS,
    verify_claim,
)
from src.schemas.evidence import SourceReference
from src.schemas.verification import EvidenceCandidate


def test_contractor_role_definition_reaches_llm():
    candidate = EvidenceCandidate(
        source=SourceReference(
            document_id="test_document",
            page_number=1,
            method="digital",
            region_index=0,
            text="Αναθέτουμε στην εταιρεία ΑΛΦΑ",
            bbox=(0, 0, 100, 20),
        ),
        retrieval_score=1.0,
        retrieval_method="test",
    )

    response = MagicMock()
    response.verdict = "supported"
    response.explanation = "Explicit award"
    response.supporting_region_indices = [0]
    response.supporting_text_anchor_indices = []
    response.considered_text_anchor_indices = []
    structured_llm = MagicMock()
    structured_llm.invoke.return_value = response

    llm = MagicMock()
    llm.with_structured_output.return_value = structured_llm

    with patch(
        "src.evaluation.claim_verifier.get_llm",
        return_value=llm,
    ):
        verify_claim(
            field_name="contractor",
            claimed_value="ΑΛΦΑ",
            candidates=[candidate],
        )

    messages = structured_llm.invoke.call_args.args[0]
    payload = json.loads(messages[1].content)

    assert payload["field_name"] == "contractor"
    assert payload["claimed_value"] == "ΑΛΦΑ"
    assert payload["role_definition"] == ROLE_DEFINITIONS["contractor"]
    assert payload["evidence"][0]["region_index"] == 0



def test_text_only_evidence_reaches_llm():
    anchor = {
        "text": "ΑΛΦΑ",
        "start": 20,
        "end": 24,
        "context": "Αναθέτουμε στην εταιρεία ΑΛΦΑ.",
        "context_start": 0,
        "context_end": 25,
    }

    response = MagicMock()
    response.verdict = "supported"
    response.explanation = "Explicit award"
    response.supporting_region_indices = []
    response.supporting_text_anchor_indices = [0]
    response.considered_text_anchor_indices = [0]
    structured_llm = MagicMock()
    structured_llm.invoke.return_value = response

    llm = MagicMock()
    llm.with_structured_output.return_value = structured_llm

    with patch(
        "src.evaluation.claim_verifier.get_llm",
        return_value=llm,
    ):
        result = verify_claim(
            field_name="contractor",
            claimed_value="ΑΛΦΑ",
            candidates=[],
            text_anchors=[anchor],
        )

    messages = structured_llm.invoke.call_args.args[0]
    payload = json.loads(messages[1].content)

    assert payload["role_definition"] == ROLE_DEFINITIONS["contractor"]
    assert payload["evidence"][0]["source_type"] == "text"
    assert payload["evidence"][0]["text"] == anchor["context"]
    assert result.verdict == "supported"
    assert result.supporting_sources == []
    assert len(result.supporting_text_anchors) == 1
    assert result.supporting_text_anchors[0].text == "ΑΛΦΑ"

def test_multi_page_text_anchors_reach_llm():
    anchors = [
        {
            "page_number": 1,
            "text": "Πρωτοδικείο Κορίνθου",
            "context": "ΠΡΩΤΟΔΙΚΕΙΟ ΚΟΡΙΝΘΟΥ",
            "start": 0,
            "end": 20,
            "context_start": 0,
            "context_end": 20,
        },
        {
            "page_number": 2,
            "text": "Πρωτοδικείο Κορίνθου",
            "context": (
                "Αναθέτουμε στην επιχείρηση ΑΛΦΑ "
                "για τις ανάγκες του Πρωτοδικείου Κορίνθου."
            ),
            "start": 55,
            "end": 75,
            "context_start": 0,
            "context_end": 100,
        },
    ]

    response = MagicMock()
    response.verdict = "insufficient_evidence"
    response.explanation = "No explicitly addressed recipient"
    response.supporting_region_indices = []
    response.supporting_text_anchor_indices = []
    response.considered_text_anchor_indices = [0, 1]

    structured_llm = MagicMock()
    structured_llm.invoke.return_value = response

    llm = MagicMock()
    llm.with_structured_output.return_value = structured_llm

    with patch(
        "src.evaluation.claim_verifier.get_llm",
        return_value=llm,
    ):
        result = verify_claim(
            field_name="recipient",
            claimed_value="Πρωτοδικείο Κορίνθου",
            candidates=[],
            text_anchors=anchors,
        )

    messages = structured_llm.invoke.call_args.args[0]
    payload = json.loads(messages[1].content)

    evidence = payload["evidence"]

    assert len(evidence) == 2
    assert evidence[0]["page_number"] == 1
    assert evidence[1]["page_number"] == 2

    assert evidence[0]["text"] == anchors[0]["context"]
    assert evidence[1]["text"] == anchors[1]["context"]

    assert result.verdict == "insufficient_evidence"
    assert result.supporting_sources == []

    # No anchor supports the recipient claim.
    assert result.supporting_text_anchors == []

    # Both page-level anchors were considered.
    assert len(result.considered_text_anchors) == 2

    assert [
        anchor.page_number
        for anchor in result.considered_text_anchors
    ] == [1, 2]

    assert [
        anchor.context
        for anchor in result.considered_text_anchors
    ] == [
        anchors[0]["context"],
        anchors[1]["context"],
    ]

    assert [
        anchor.page_number
        for anchor in result.considered_text_anchors
    ] == [1, 2]



def test_invalid_text_anchor_indices_are_ignored():
    anchor = {
        "text": "ΑΛΦΑ",
        "start": 20,
        "end": 24,
        "context": "Αναθέτουμε στην εταιρεία ΑΛΦΑ.",
        "context_start": 0,
        "context_end": 30,
        "page_number": 1,
        "document_id": "test_document",
        "method": "digital",
    }

    response = MagicMock()
    response.verdict = "supported"
    response.explanation = "Explicit award"
    response.supporting_region_indices = []
    response.supporting_text_anchor_indices = [
        0, 99, -1, True, 0
    ]
    response.considered_text_anchor_indices = [
        0, 99, -1, True, 0
    ]

    structured_llm = MagicMock()
    structured_llm.invoke.return_value = response

    llm = MagicMock()
    llm.with_structured_output.return_value = structured_llm

    with patch(
        "src.evaluation.claim_verifier.get_llm",
        return_value=llm,
    ):
        result = verify_claim(
            field_name="contractor",
            claimed_value="ΑΛΦΑ",
            candidates=[],
            text_anchors=[anchor],
        )

    assert len(result.supporting_text_anchors) == 1
    assert len(result.considered_text_anchors) == 1
    assert result.supporting_text_anchors[0].page_number == 1
