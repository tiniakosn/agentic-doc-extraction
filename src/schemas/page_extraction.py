from typing import Literal
from pydantic import BaseModel, Field, model_validator


class ExtractedField(BaseModel):
    value: str | None = None
    status: Literal["present", "not_present", "uncertain"]
    evidence: str | None = None

    @model_validator(mode="after")
    def check_consistency(self):
        if self.status == "present":
            if not self.value or not self.evidence:
                raise ValueError(
                    "Present fields require value and evidence"
                )
        elif self.status == "not_present":
            if self.value is not None:
                raise ValueError(
                    "Not-present fields cannot have a value"
                )
        return self


class PageExtraction(BaseModel):
    document_type: ExtractedField
    issuing_authority: ExtractedField
    recipient: ExtractedField
    contractor: ExtractedField
    contractor_tax_id: ExtractedField