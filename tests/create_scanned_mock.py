import pymupdf as fitz
from pathlib import Path

def create_scanned_pdf(input_pdf: str, output_pdf: str):
    doc = fitz.open(input_pdf)
    scanned_doc = fitz.open()

    for page in doc:
        # Μετατροπή της σελίδας σε εικόνα (Rasterization)
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")

        # Δημιουργία νέας κενής σελίδας με την εικόνα
        new_page = scanned_doc.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(page.rect, stream=img_bytes)

    scanned_doc.save(output_pdf)
    print(f"[OK] Δημιουργήθηκε το scanned mock PDF: {output_pdf}")

if __name__ == "__main__":
    Path("data/raw").mkdir(exist_ok=True)
    create_scanned_pdf("data/raw/doc_1_digital.pdf", "data/raw/doc_4_scanned.pdf")