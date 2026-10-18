import pymupdf as fitz
from pathlib import Path
from typing import Tuple, List
import io

def select_key_page_indices(total_pages: int) -> List[int]:
    """
    Επιλέγει τις πιο κρίσιμες σελίδες για εξαγωγή:
    - Αν <= 4 σελίδες: Όλες.
    - Αν > 4 σελίδες: Οι 2 πρώτες (Θέμα/ΑΔΑ) και οι 2 τελευταίες (Απόφαση/Ανάδοχος/Υπογραφές).
    """
    if total_pages <= 4:
        return list(range(total_pages))
    
    # 2 πρώτες και 2 τελευταίες σελίδες
    return [0, 1, total_pages - 2, total_pages - 1]

def analyze_pdf_density(pdf_path: Path, min_chars_per_page: int = 50) -> Tuple[str, str, List[bytes]]:
    """
    Αναλύει το PDF και αποφασίζει τη διαδρομή επεξεργασίας:
    - 'digital': Το έγγραφο έχει ψηφιακό κείμενο.
    - 'scanned': Το έγγραφο είναι σαρωμένη εικόνα και χρειάζεται Vision/OCR.

    Επιστρέφει:
    - track: 'digital' | 'scanned'
    - extracted_text: Το ψηφιακό κείμενο (αν υπάρχει)
    - page_images: Λίστα με εικόνες (PNG bytes) των σελίδων αν είναι scanned
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    if total_pages == 0:
        return "scanned", "", []

    all_text = []
    for page_idx in range(total_pages):
        page = doc[page_idx]
        text = page.get_text("text").strip()
        all_text.append(text)

    combined_text = "\n\n".join(all_text).strip()
    avg_chars = len(combined_text) / total_pages

    if avg_chars >= min_chars_per_page:
        return "digital", combined_text, []

    # Scanned track: εξαγωγή των κρίσιμων σελίδων ως εικόνες
    page_images: List[bytes] = []
    target_indices = select_key_page_indices(total_pages)

    for idx in target_indices:
        page = doc[idx]
        pix = page.get_pixmap(dpi=150)  # 150 DPI επαρκεί για ανάγνωση κειμένου
        img_bytes = pix.tobytes("png")
        page_images.append(img_bytes)

    return "scanned", combined_text, page_images