import numpy as np
import re
from dataclasses import dataclass
import unicodedata
import pymupdf


@dataclass(frozen=True)
class PageQuality:
    text_chars: int
    image_count: int
    image_coverage: float
    suspicious_text_ratio: float
    visual_ink_ratio: float
    greek_letter_ratio: float
    unassigned_char_count: int = 0

def calculate_image_coverage(page: pymupdf.Page) -> float:
    page_area = page.rect.get_area()

    if page_area <= 0:
        return 0.0

    image_rects = []

    for image in page.get_images(full=True):
        xref = image[0]

        for rect in page.get_image_rects(xref):
            visible = rect & page.rect

            if not visible.is_empty:
                image_rects.append(visible)

    covered_area = sum(
        rect.get_area()
        for rect in image_rects
    )

    return min(covered_area / page_area, 1.0)


def calculate_suspicious_text_ratio(text: str) -> float:
    if not text:
        return 0.0

    suspicious_chars = sum(
        char in {"�", "∕", "�"}
        for char in text
    )

    return suspicious_chars / len(text)


def assess_page_quality(page: pymupdf.Page) -> PageQuality:
    text = page.get_text("text")

    return PageQuality(
        text_chars=len(text.strip()),
        image_count=len(page.get_images(full=True)),
        image_coverage=round(
            calculate_image_coverage(page), 4
        ),
        suspicious_text_ratio=round(
            calculate_suspicious_text_ratio(text), 4
        ),
        visual_ink_ratio=round(
            calculate_visual_ink_ratio(page), 4
        ),
        greek_letter_ratio=round(
            calculate_greek_letter_ratio(text), 4
        ),
        unassigned_char_count=count_unassigned_chars(text),
        
    )

def calculate_visual_ink_ratio(page: pymupdf.Page, dpi: int = 72) -> float:
    pix = page.get_pixmap(
        dpi=dpi,
        colorspace=pymupdf.csGRAY,
        alpha=False,
    )

    pixels = np.frombuffer(
        pix.samples,
        dtype=np.uint8,
    ).reshape(pix.height, pix.width)

    return float(np.mean(pixels < 220))

def calculate_greek_letter_ratio(text: str) -> float:
    letters = sum(char.isalpha() for char in text)

    if letters == 0:
        return 0.0

    greek = len(re.findall(
        r"[Α-Ωα-ωΆ-Ώά-ώ]",
        text,
    ))

    return greek / letters

def count_unassigned_chars(text: str) -> int:
    """Count Unicode characters without an assigned code point."""
    return sum(
        unicodedata.category(char) == "Cn"
        for char in text
    )