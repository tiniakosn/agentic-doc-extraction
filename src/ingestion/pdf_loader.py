
from pathlib import Path

import pymupdf

from src.schemas.document import (
    DocumentRecord,
    DocumentPage,
    TextLayer,
    TextRegion,
)


def extract_digital_regions(page: pymupdf.Page) -> list[TextRegion]:
    """Extract digital text lines with PDF-space coordinates."""

    regions = []

    page_width = page.rect.width
    page_height = page.rect.height

    data = page.get_text("dict")

    for block in data["blocks"]:
        if block.get("type") != 0:
            continue

        for line in block.get("lines", []):
            text = "".join(
                span["text"]
                for span in line.get("spans", [])
            ).strip()

            if not text:
                continue

            x1, y1, x2, y2 = line["bbox"]


            # Clip normalized coordinates to the visible PDF page.
            # Preserve the original PDF-space bounding box.
            nx1 = max(0.0, min(1.0, x1 / page_width))
            ny1 = max(0.0, min(1.0, y1 / page_height))
            nx2 = max(0.0, min(1.0, x2 / page_width))
            ny2 = max(0.0, min(1.0, y2 / page_height))

            normalized_bbox = (
                (nx1, ny1, nx2, ny2)
                if nx1 < nx2 and ny1 < ny2
                else None
            )


            regions.append(
                TextRegion(
                    text=text,
                    bbox=(x1, y1, x2, y2),
                    normalized_bbox=normalized_bbox,
                    confidence=None,
                )
            )

    return regions


def load_document(pdf_path: str | Path) -> DocumentRecord:
    pdf_path = Path(pdf_path)

    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)

    pages = []

    with pymupdf.open(pdf_path) as pdf:
        for index, page in enumerate(pdf):
            digital_regions = extract_digital_regions(page)

            pages.append(
                DocumentPage(
                    page_number=index + 1,
                    text_layers=[
                        TextLayer(
                            method="digital",
                            text=page.get_text("text"),
                            regions=digital_regions,
                        )
                    ],
                )
            )

    return DocumentRecord(
        document_id=pdf_path.stem,
        source="diavgeia",
        pages=pages,
        metadata={"filename": pdf_path.name},
    )
