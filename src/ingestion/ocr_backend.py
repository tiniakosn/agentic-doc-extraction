from time import perf_counter

import pymupdf
import pytesseract
from PIL import Image

from src.schemas.document import TextLayer


def run_tesseract(
    pdf_path: str,
    page_number: int,
    dpi: int = 300,
) -> TextLayer:
    start = perf_counter()

    with pymupdf.open(pdf_path) as pdf:
        if not 1 <= page_number <= len(pdf):
            raise ValueError("Invalid page number")

        page = pdf[page_number - 1]
        pix = page.get_pixmap(dpi=dpi, alpha=False)

        image = Image.frombytes(
            "RGB",
            (pix.width, pix.height),
            pix.samples,
        )

        text = pytesseract.image_to_string(
            image,
            lang="ell+eng",
            config="--psm 3",
        )

    return TextLayer(
        method="tesseract",
        text=text,
        model_name="tesseract-5.3.4",
        latency_seconds=round(perf_counter() - start, 3),
    )

from pathlib import Path


class TesseractProcessor:
    def __init__(self, dpi: int = 300):
        self.dpi = dpi

    def process_page(
        self,
        pdf_path: str | Path,
        page_number: int,
    ) -> TextLayer:
        return run_tesseract(
            str(pdf_path),
            page_number=page_number,
            dpi=self.dpi,
        )