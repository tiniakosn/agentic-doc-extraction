from pathlib import Path

import pymupdf

from src.ingestion.page_quality import assess_page_quality
from src.ingestion.routing import choose_processing_route_v2


PDF_FILES = [
    Path("data/discovery/63ΤΞ46ΜΦΟΤ-ΑΟΟ.pdf"),
    Path("data/discovery/65ΓΦ6-Θ5Μ.pdf"),
]


for pdf_path in PDF_FILES:
    with pymupdf.open(pdf_path) as doc:
        page = doc[0]

        quality = assess_page_quality(page)
        decision = choose_processing_route_v2(quality)

    print(f"\nDocument: {pdf_path.name}")
    print(f"Text characters: {quality.text_chars}")
    print(f"Greek ratio: {quality.greek_letter_ratio}")
    print(f"Suspicious ratio: {quality.suspicious_text_ratio}")
    print(f"Visual ink ratio: {quality.visual_ink_ratio}")
    print(f"Image coverage: {quality.image_coverage}")
    print(f"Selected route: {decision.route}")
    print(f"Reason: {decision.reason}")