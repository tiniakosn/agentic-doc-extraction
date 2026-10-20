from typing import Any

from src.evaluation.region_grounding import find_matching_regions
from src.schemas.evidence import SourceReference


def anchor_value(
    value: str,
    regions: list[dict[str, Any]],
    *,
    document_id: str,
    page_number: int,
    method: str,
    image_width: int | None = None,
    image_height: int | None = None,
    min_score: float = 0.85,
) -> list[SourceReference]:
    """Connect an extracted value to real OCR regions."""

    if (image_width is None) != (image_height is None):
        raise ValueError("Both image dimensions must be provided together")

    matches = find_matching_regions(
        value,
        regions,
        min_score=min_score,
    )

    references = []

    for match in matches:
        region = regions[match.region_index]

        normalized_bbox = region.get("normalized_bbox")

        if normalized_bbox is None and image_width and image_height:
            x1, y1, x2, y2 = match.bbox
            normalized_bbox = (
                x1 / image_width,
                y1 / image_height,
                x2 / image_width,
                y2 / image_height,
            )

        references.append(
            SourceReference(
                document_id=document_id,
                page_number=page_number,
                method=method,
                region_index=match.region_index,
                text=match.text,
                bbox=match.bbox,
                normalized_bbox=normalized_bbox,
            )
        )

    return references