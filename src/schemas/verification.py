
from typing import Literal

from pydantic import BaseModel, Field

from src.schemas.evidence import SourceReference


class EvidenceCandidate(BaseModel):
    source: SourceReference
    retrieval_score: float = Field(ge=0, le=1)
    retrieval_method: str


class ClaimVerification(BaseModel):
    field_name: str
    claimed_value: str | None

    verdict: Literal[
        "supported",
        "contradicted",
        "insufficient_evidence",
        "not_checked",
    ]

    supporting_sources: list[SourceReference] = Field(
        default_factory=list
    )

    explanation: str
    verification_method: str
