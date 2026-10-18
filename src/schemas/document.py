from typing import Literal

from pydantic import BaseModel, Field


ExtractionMethod = Literal[
    "digital",
    "tesseract",
    "paddleocr",
    "vlm",
]

class TextRegion(BaseModel):
    text: str
    bbox: tuple[float, float, float, float]
    confidence: float | None = Field(default=None, ge=0, le=1)
    normalized_bbox: tuple[float, float, float, float] | None = None

class TextLayer(BaseModel):
    method: ExtractionMethod
    text: str
    model_name: str | None = None
    latency_seconds: float | None = None
    regions: list[TextRegion] = Field(default_factory=list)
    image_width: int | None = Field(default=None, gt=0)
    image_height: int | None = Field(default=None, gt=0)


class DocumentPage(BaseModel):
    page_number: int = Field(ge=1)
    text_layers: list[TextLayer] = Field(default_factory=list)
    image_coverage: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )


class DocumentRecord(BaseModel):
    document_id: str
    source: str
    pages: list[DocumentPage] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)