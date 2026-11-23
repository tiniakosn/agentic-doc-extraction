
from typing import Literal

from pydantic import BaseModel, Field


class PageFieldEvidence(BaseModel):
    page_number: int = Field(ge=1)
    value: str
    evidence: str


class DocumentField(BaseModel):
    status: Literal[
        "present",
        "not_present",
        "uncertain",
        "conflict",
    ]

    value: str | None = None

    sources: list[PageFieldEvidence] = Field(
        default_factory=list
    )

    notes: str = ""


class DocumentExtraction(BaseModel):
    document_id: str
    page_count: int = Field(ge=1)

    fields: dict[str, DocumentField]
