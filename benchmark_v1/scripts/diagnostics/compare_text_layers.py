from pathlib import Path
from time import perf_counter

import pymupdf

from src.ingestion.ocr_backend import TesseractProcessor


PDF_PATH = Path("data/discovery/63ΤΞ46ΜΦΟΤ-ΑΟΟ.pdf")
PAGE_NUMBER = 1

OUTPUT_DIR = Path(
    "text_layer_comparison/63ΤΞ46ΜΦΟΤ-ΑΟΟ"
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# 1. Extract the existing digital text layer.
start = perf_counter()

with pymupdf.open(PDF_PATH) as doc:
    digital_text = doc[PAGE_NUMBER - 1].get_text("text")

digital_duration = perf_counter() - start


# 2. Run OCR on the rendered PDF page.
processor = TesseractProcessor(dpi=300)

start = perf_counter()

ocr_layer = processor.process_page(
    str(PDF_PATH),
    PAGE_NUMBER,
)

ocr_duration = perf_counter() - start
ocr_text = ocr_layer.text


# 3. Save both outputs for inspection.
(OUTPUT_DIR / "digital.txt").write_text(
    digital_text,
    encoding="utf-8",
)

(OUTPUT_DIR / "tesseract.txt").write_text(
    ocr_text,
    encoding="utf-8",
)


# 4. Print basic diagnostic information.
print("DIGITAL TEXT")
print("Characters:", len(digital_text))
print("Duration:", round(digital_duration, 3), "sec")

print("\nTESSERACT OCR")
print("Characters:", len(ocr_text))
print("Duration:", round(ocr_duration, 3), "sec")

print("\nKEY TERMS")
terms = [
    "ΔΗΜΟΣ ΑΝΑΤΟΛΙΚΗΣ ΣΑΜΟΥ",
    "ΔΗΜΗΤΡΙΟΣ ΚΑΝΑΡΗΣ",
    "801033798",
    "Απευθείας ανάθεση",
]

for term in terms:
    print(
        f"{term:15} | "
        f"Digital: {term.casefold() in digital_text.casefold()} | "
        f"OCR: {term.casefold() in ocr_text.casefold()}"
    )

print("\nFiles saved to:", OUTPUT_DIR)