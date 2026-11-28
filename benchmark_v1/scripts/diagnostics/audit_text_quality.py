from pathlib import Path

import pymupdf

from src.ingestion.page_quality import assess_page_quality
from src.ingestion.routing import choose_processing_route_v2


PDF_DIR = Path("data/discovery")

DOCUMENTS = [
    "63ΤΞ46ΜΦΟΤ-ΑΟΟ.pdf",
    "65ΓΦ6-Θ5Μ.pdf",
    "685Κ465274-Χ1Ψ.pdf",
    "91ΤΣ46ΝΙΦ6-ΠΡΛ.pdf",
    "ΕΟΣΩ46ΨΖΣΠ-ΠΣΜ.pdf",
    "Ρ5ΑΓ7ΛΨ-Υ8Ρ.pdf",
    "ΨΓΥΖ4ΧΡ-3Θ3.pdf",
    "ΨΡ6Ξ469ΗΡΘ-7ΝΗ.pdf",
]


for filename in DOCUMENTS:
    path = PDF_DIR / filename

    with pymupdf.open(path) as document:
        page = document[0]

        quality = assess_page_quality(page)
        decision = choose_processing_route_v2(quality)
        text = page.get_text("text")

    print("\n" + "=" * 60)
    print("PDF:", filename)
    print("Characters:", quality.text_chars)
    print("Greek ratio:", quality.greek_letter_ratio)
    print("Suspicious ratio:", quality.suspicious_text_ratio)
    print("Route:", decision.route)
    print("Text sample:", repr(text[:250]))