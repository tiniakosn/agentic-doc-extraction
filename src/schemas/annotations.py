from decimal import Decimal
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, model_validator, Field

T = TypeVar("T")


class Evidence(BaseModel):
    page: int | None = None
    text: str


class Annotation(BaseModel, Generic[T]):
    value: T | None
    status: Literal["present", "not_present"]
    evidence: Evidence | None = None

    @model_validator(mode="after")
    def validate_annotation_state(self):
        if self.status == "present":
            if self.value is None:
                raise ValueError(
                    "A present annotation must have a value."
                )

            if self.evidence is None:
                raise ValueError(
                    "A present annotation must have evidence."
                )

        if self.status == "not_present" and self.value is not None:
            raise ValueError(
                "A not_present annotation cannot have a value."
            )

        return self


class ContractorAnnotation(BaseModel):
    name: Annotation[str]
    tax_id: Annotation[str]

class FinancialAnnotation(BaseModel):
    net_amount: Annotation[Decimal]
    vat_rate: Annotation[Decimal]
    total_amount: Annotation[Decimal]

class DocumentAnnotation(BaseModel):
    document_id: str
    document_type: str | None = None
    contractor: ContractorAnnotation
    financials: FinancialAnnotation
    notes: list[str] = Field(default_factory=list)