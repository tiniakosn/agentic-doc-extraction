
import json
import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from typing import Literal

from src.extraction.llm_client import get_llm, unwrap_structured
from src.schemas.verification import (
    EvidenceCandidate,
    ClaimVerification,
    TextEvidenceReference,
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
    supporting_text_anchor_indices: list[int] = Field(
        default_factory=list
    )
    considered_text_anchor_indices: list[int] = Field(
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

8. Return supporting_text_anchor_indices only from the
   supplied text anchor candidates.

Text anchor indices are zero-based and are separate
from region indices.

Never invent evidence indices.

Evidence reference requirements:

1. considered_text_anchor_indices identifies the
   excerpts materially considered in the decision.

2. supporting_text_anchor_indices identifies only
   excerpts that directly establish the claimed role.

3. When verdict is insufficient_evidence,
   supporting_text_anchor_indices must be empty.

4. Entity mentions and contextual role references
   may be considered without supporting the claimed role.

5. For recipient, mentioning a final beneficiary or
   budget holder does not establish explicit recipient status.

6. Always provide a concise, evidence-based explanation
   in 1-3 complete sentences.

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
                "text_anchor_index": index,
                "document_id": anchor.get("document_id"),
                "page_number": anchor.get("page_number"),
                "method": anchor.get("method"),
                "text": anchor["context"],
                "matched_text": anchor["text"],
                "start": anchor["start"],
                "end": anchor["end"],
                "context_start": anchor["context_start"],
                "context_end": anchor["context_end"],
            }
            for index, anchor in enumerate(text_anchors)
        )



    llm = get_llm(model_name=model_name)
    structured_llm = llm.with_structured_output(
        ClaimAssessment,
        include_raw=True,
    )

    start = time.perf_counter()
    raw_response = structured_llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=json.dumps({
            "field_name": field_name,
            "claimed_value": claimed_value,
            "role_definition": ROLE_DEFINITIONS.get(field_name),
            "evidence": evidence,
        }, ensure_ascii=False)),
    ])

    # Real calls return {"raw", "parsed"}; test mocks may return the object directly.
    if isinstance(raw_response, dict) and "parsed" in raw_response:
        response = unwrap_structured(
            raw_response,
            ClaimAssessment,
            call_type="claim_verification",
            model=model_name,
            latency_s=time.perf_counter() - start,
            extra={"field": field_name},
        )
    else:
        response = raw_response

    by_index = {
        c.source.region_index: c.source
        for c in candidates
    }

    selected_sources = [
        by_index[index]
        for index in response.supporting_region_indices
        if index in by_index
    ]



    def build_text_references(indices):
        selected = []
        seen_indices = set()

        if not isinstance(indices, (list, tuple)):
            return selected

        for index in indices:
            if (
                not isinstance(index, int)
                or isinstance(index, bool)
                or index < 0
                or index >= len(text_anchors or [])
                or index in seen_indices
            ):
                continue

            seen_indices.add(index)
            anchor = text_anchors[index]

            selected.append(
                TextEvidenceReference(
                    document_id=anchor.get("document_id"),
                    page_number=anchor.get("page_number"),
                    method=anchor.get("method"),
                    text=anchor["text"],
                    start=anchor["start"],
                    end=anchor["end"],
                    context=anchor["context"],
                    context_start=anchor["context_start"],
                    context_end=anchor["context_end"],
                )
            )

        return selected

    considered_text_anchors = build_text_references(
        getattr(response, "considered_text_anchor_indices", [])
    )

    # Supporting evidence must establish the claimed role.
    # A non-supported verdict cannot carry supporting anchors.
    supporting_indices = (
        response.supporting_text_anchor_indices
        if response.verdict == "supported"
        else []
    )

    selected_text_anchors = build_text_references(
        supporting_indices
    )



    return ClaimVerification(
        field_name=field_name,
        claimed_value=claimed_value,
        verdict=response.verdict,
        supporting_sources=selected_sources,
        explanation=response.explanation,
        verification_method="llm_evidence_verification",
        supporting_text_anchors=selected_text_anchors,
        considered_text_anchors=considered_text_anchors,
    )
