
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


def test_multi_page_text_anchors_reach_llm():
    anchors = [
        {
            "page_number": 1,
            "text": "Πρωτοδικείο Κορίνθου",
            "context": "ΠΡΩΤΟΔΙΚΕΙΟ ΚΟΡΙΝΘΟΥ",
            "start": 0,
            "end": 20,
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
        },
    ]

    response = MagicMock()
    response.verdict = "insufficient_evidence"
    response.explanation = "No explicitly addressed recipient"
    response.supporting_region_indices = []

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
