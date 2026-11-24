
from typing import Literal

from pydantic import BaseModel, Field
from pydantic import BaseModel, Field, model_validator
from src.schemas.evidence import SourceReference


class EvidenceCandidate(BaseModel):
    source: SourceReference
    retrieval_score: float = Field(ge=0, le=1)
    retrieval_method: str



class TextEvidenceReference(BaseModel):
    """Text evidence with page-level character provenance."""

    document_id: str | None = None
    page_number: int | None = Field(default=None, ge=1)
    method: str | None = None

    text: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)

    context: str
    context_start: int = Field(ge=0)
    context_end: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_offsets(self):
        if self.start >= self.end:
            raise ValueError("Invalid text anchor offsets")

        if not (
            self.context_start
            <= self.start
            < self.end
            <= self.context_end
        ):
            raise ValueError("Text anchor outside context")

        return self


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
    supporting_text_anchors: list[TextEvidenceReference] = Field(
        default_factory=list
    )

    considered_text_anchors: list[TextEvidenceReference] = Field(
        default_factory=list
    )

    explanation: str
    verification_method: str
