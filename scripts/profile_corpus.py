import json
from pathlib import Path

import pymupdf
import csv

PDF_DIR = Path("data/discovery")
METADATA_DIR = Path("data/metadata")


def profile_document(pdf_path: Path) -> dict:
    metadata_path = METADATA_DIR / f"{pdf_path.stem}.json"

    metadata = json.loads(
        metadata_path.read_text(encoding="utf-8")
    )

    decision = metadata["decision"]

    with pymupdf.open(pdf_path) as doc:
        page_count = len(doc)
        text_chars = sum(
            len(page.get_text("text"))
            for page in doc
        )

    return {
        "ada": pdf_path.stem,
        "decision_type": decision["decisionTypeId"],
        "page_count": page_count,
        "text_chars": text_chars,
    }

def calculate_image_coverage(page) -> float:
    page_area = page.rect.get_area()

    if page_area == 0:
        return 0.0

    image_rects = []

    for image in page.get_images(full=True):
        xref = image[0]

        for rect in page.get_image_rects(xref):
            visible_rect = rect & page.rect

            if not visible_rect.is_empty:
                image_rects.append(visible_rect)

    if not image_rects:
        return 0.0

    # Approximation: overlapping image regions may be counted twice.
    covered_area = sum(rect.get_area() for rect in image_rects)

    return round(min(covered_area / page_area, 1.0), 4)

def profile_pages(pdf_path: Path) -> list[dict]:
    results = []

    with pymupdf.open(pdf_path) as doc:
        for page_index, page in enumerate(doc):
            text = page.get_text("text")

            results.append({
                "ada": pdf_path.stem,
                "page": page_index + 1,
                "text_chars": len(text.strip()),
                "image_count": len(page.get_images(full=True)),
                "page_width": round(page.rect.width, 2),
                "page_height": round(page.rect.height, 2),
                "image_coverage": calculate_image_coverage(page),
            })

    return results

def main():
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    
    results = []
    

    for pdf_path in pdf_files:
        profile = profile_document(pdf_path)
        results.append(profile)

    page_results = []

    for pdf_path in pdf_files:
        page_results.extend(profile_pages(pdf_path))

    output_path = Path("evaluation_results/corpus_profile.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "ada",
                "decision_type",
                "page_count",
                "text_chars",
                
            ],
        )
        writer.writeheader()
        writer.writerows(results)
    
    page_output = Path("evaluation_results/page_profile.csv")

    with page_output.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "ada",
                "page",
                "text_chars",
                "image_count",
                "image_coverage",
                "page_width",
                "page_height",
                
            ],
        )
        writer.writeheader()
        writer.writerows(page_results)

    print(f"Profiled {len(page_results)} pages")

    print(f"Profiled {len(results)} documents")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()