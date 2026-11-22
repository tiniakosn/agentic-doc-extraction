
import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from typing import Literal

from src.extraction.llm_client import get_llm
from src.schemas.verification import (
    EvidenceCandidate,
    ClaimVerification,
)


class ClaimAssessment(BaseModel):
    verdict: Literal[
        "supported",
        "contradicted",
        "insufficient_evidence",
    ]
    explanation: str = Field(min_length=1)
    supporting_region_indices: list[int] = Field(
        default_factory=list
    )


SYSTEM_PROMPT = """
You are a careful verifier of extracted information
from Greek administrative and procurement documents.

Your task is to verify whether the supplied source excerpts
support the specific extracted claim.

Rules:
1. Use ONLY the supplied source excerpts.
2. Distinguish mentioning an entity from proving its role.
3. Treat different Greek grammatical forms as potentially equivalent.
4. Do not infer missing facts.
5. If evidence is ambiguous, return insufficient_evidence.
6. Return supporting region indices only from the supplied candidates.
7. A retrieval score is not proof of correctness.


Role verification requirements:

Evaluate the claimed FIELD ROLE, not merely whether the
claimed entity or value appears in the source.

For recipient:
- Require evidence that the person or organization is
  explicitly addressed by the current document.
- A contractual counterparty, signatory, beneficiary,
  or mentioned person is not automatically a recipient.

For contractor:
- Require evidence of an explicit award or a performing
  counterparty in a concluded work/service contract.
- A payment allocation, budget commitment, invitation,
  or mention of a supplier does not by itself establish
  an awarded contractor.

For contractor_tax_id:
- First establish the contractor's role.
- Then establish that the tax ID is linked to that
  contractor in the supplied evidence.
- Format and checksum validity do not prove the role.

Verdict policy:
- supported: the supplied evidence establishes the
  specific claimed role.
- contradicted: the supplied evidence explicitly
  conflicts with the claimed role.
- insufficient_evidence: the claimed role cannot be
  established from the supplied evidence.

Do not use contradicted merely because an explicit
role statement is absent.

Before returning supported, explain which source
statement establishes the claimed role.
If the evidence only establishes entity presence,
return insufficient_evidence.

"""


ROLE_DEFINITIONS = {
    "recipient": (
        "The person or organization explicitly addressed by "
        "the current document. A contractor, applicant or "
        "mentioned person is not automatically a recipient."
    ),
    "contractor": (
        "A person or organization explicitly awarded goods, "
        "works or services, or the performing counterparty "
        "of a concluded work/service contract. "
        "A mentioned supplier, invitee or payment beneficiary "
        "is not automatically an awarded contractor."
    ),
    "contractor_tax_id": (
        "A tax identification number explicitly linked to "
        "the contractor established by the document. "
        "A valid tax ID belonging to another entity must "
        "not be accepted as contractor_tax_id."
    ),
}



def verify_claim(
    field_name: str,
    claimed_value: str,
    candidates: list[EvidenceCandidate],
    model_name: str = "qwen/qwen3.8-27b",
    text_anchors: list[dict] | None = None,
) -> ClaimVerification:

    if not candidates and not text_anchors:
        return ClaimVerification(
            field_name=field_name,
            claimed_value=claimed_value,
            verdict="insufficient_evidence",
            explanation="No evidence candidates were retrieved.",
            verification_method="no_candidates",
        )

    evidence = [
        {
            "region_index": c.source.region_index,
            "text": c.source.text,
        }
        for c in candidates
    ]

    if text_anchors:
        evidence.extend(
            {
                "source_type": "text",
                "text": anchor["context"],
                "start": anchor["start"],
                "end": anchor["end"],
            }
            for anchor in text_anchors
        )

    llm = get_llm(model_name=model_name)
    structured_llm = llm.with_structured_output(
        ClaimAssessment
    )

    response = structured_llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=json.dumps({
            "field_name": field_name,
            "claimed_value": claimed_value,
            "role_definition": ROLE_DEFINITIONS.get(field_name),
            "evidence": evidence,
        }, ensure_ascii=False)),
    ])

    by_index = {
        c.source.region_index: c.source
        for c in candidates
    }

    selected_sources = [
        by_index[index]
        for index in response.supporting_region_indices
        if index in by_index
    ]

    return ClaimVerification(
        field_name=field_name,
        claimed_value=claimed_value,
        verdict=response.verdict,
        supporting_sources=selected_sources,
        explanation=response.explanation,
        verification_method="llm_evidence_verification",
    )
