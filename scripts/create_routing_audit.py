
import csv
import random
from collections import defaultdict
from pathlib import Path

import pymupdf


random.seed(42)

PDF_DIR = Path("data/discovery")
ROUTING_CSV = Path("evaluation_results/routing_analysis.csv")
OUTPUT = Path("evaluation_results/routing_audit.pdf")


def main():
    groups = defaultdict(list)

    with ROUTING_CSV.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            groups[row["route"]].append(row)

    output = pymupdf.open()

    for route in ("digital", "tesseract", "review"):
        sample = random.sample(
            groups[route],
            min(5, len(groups[route])),
        )

        for item in sample:
            pdf_path = PDF_DIR / f"{item['ada']}.pdf"
            page_number = int(item["page"])

            with pymupdf.open(pdf_path) as source:
                source_page = source[page_number - 1]

                audit_page = output.new_page(
                    width=595,
                    height=842,
                )

                header = (
                    f"Route: {route.upper()} | "
                    f"ADA: {item['ada']} | "
                    f"Page: {page_number}"
                )

                audit_page.insert_text(
                    (30, 30),
                    header,
                    fontsize=10,
                )

                target_rect = pymupdf.Rect(
                    30, 55, 565, 810
                )

                audit_page.show_pdf_page(
                    target_rect,
                    source,
                    page_number - 1,
                    keep_proportion=True,
                )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    output.save(OUTPUT)
    output.close()

    print("Saved:", OUTPUT)


if __name__ == "__main__":
    main()
