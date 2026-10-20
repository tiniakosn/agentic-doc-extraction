
from pydantic import BaseModel, Field, model_validator


class SourceReference(BaseModel):
    document_id: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    method: str
    region_index: int = Field(ge=0)

    text: str
    bbox: tuple[float, float, float, float]
    normalized_bbox: tuple[float, float, float, float] | None = None

    @model_validator(mode="after")
    def validate_coordinates(self):
        x1, y1, x2, y2 = self.bbox

        if x1 >= x2 or y1 >= y2:
            raise ValueError("Invalid bounding box coordinates")

        if self.normalized_bbox is not None:
            nx1, ny1, nx2, ny2 = self.normalized_bbox

            if not (
                0 <= nx1 < nx2 <= 1
                and 0 <= ny1 < ny2 <= 1
            ):
                raise ValueError("Invalid normalized coordinates")

        return self
