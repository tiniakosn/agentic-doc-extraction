
import csv
from collections import Counter
from pathlib import Path

import pymupdf

from src.ingestion.page_quality import assess_page_quality
from src.ingestion.routing import choose_processing_route


PDF_DIR = Path("data/discovery")
OUTPUT_PATH = Path("evaluation_results/routing_analysis.csv")


def main():
    records = []

    for pdf_path in sorted(PDF_DIR.glob("*.pdf")):
        with pymupdf.open(pdf_path) as doc:
            for page_index, page in enumerate(doc):
                quality = assess_page_quality(page)
                decision = choose_processing_route(quality)

                records.append({
                    "ada": pdf_path.stem,
                    "page": page_index + 1,
                    "text_chars": quality.text_chars,
                    "image_coverage": quality.image_coverage,
                    "suspicious_text_ratio": quality.suspicious_text_ratio,
                    "route": decision.route,
                    "reason": decision.reason,
                })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "ada",
                "page",
                "text_chars",
                "image_coverage",
                "suspicious_text_ratio",
                "route",
                "reason",
            ],
        )
        writer.writeheader()
        writer.writerows(records)

    counts = Counter(record["route"] for record in records)

    print("Total pages:", len(records))
    print("Routing distribution:")

    for route in ("digital", "tesseract", "review"):
        print(f"  {route}: {counts[route]}")

    print("Saved:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
