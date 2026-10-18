import re
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from pypdf import PdfReader

from src.utils.density_router import analyze_pdf_density
from src.utils.ocr_strategy import get_ocr_engine



def normalize_greek_text(text: str) -> str:
    """
    Καθαρίζει και διορθώνει κοινά σφάλματα κωδικοποίησης και στοίχισης:
    - Broken CMaps παλαιών fonts.
    - Ένωση λέξεων που χωρίστηκαν με παύλα στο τέλος γραμμής.
    - Συμπύκνωση πολλαπλών κενών/tabs.
    """
    if not text:
        return ""

    # 1. Βασική αποκατάσταση γνωστών σφαλμάτων γραμματοσειράς
    text = re.sub(r'ευρϊ\b', 'ευρώ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bζναντι\b', 'έναντι', text, flags=re.IGNORECASE)
    text = re.sub(r'μιςκϊματοσ', 'μισθώματος', text, flags=re.IGNORECASE)

    # 2. Ένωση συλλαβισμένων λέξεων στο τέλος γραμμής
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

    # 3. Συμπύκνωση κενών και tabs
    text = re.sub(r'[ \t]+', ' ', text)

    # 4. Περιορισμός συνεχόμενων κενών γραμμών
    text = re.sub(r'\n\s*\n+', '\n\n', text)

    return text.strip()


def extract_ada_from_annotations(reader: PdfReader) -> Optional[str]:
    """Σαρώνει τα annotations των σελίδων για ΑΔΑ (Ψηφιακά PDFs)."""
    ada_pattern = re.compile(r'ΑΔΑ\s*[:\.]?\s*([A-Z0-9Α-Ω0-9\-]+)', re.IGNORECASE)

    for page in reader.pages:
        if "/Annots" in page:
            annotations = page["/Annots"]
            for annot in annotations:
                obj = annot.get_object()
                contents = str(obj.get("/Contents", ""))
                match = ada_pattern.search(contents)
                if match:
                    code = match.group(1).strip()
                    if "-" in code and len(code) >= 12:
                        return code
    return None


def extract_ada_from_text(text: str) -> Optional[str]:
    """
    Ανθεκτικός εντοπισμός ΑΔΑ μέσω Regex στο σώμα του κειμένου (OCR/Scanned).
    Αναγνωρίζει μοτίβα τύπου: Ψ00Γ46ΜΤΛΒ-3ΒΖ
    """
    # 1. Αναζήτηση με πρόθεμα ΑΔΑ
    match = re.search(r'ΑΔΑ\s*[:\.\-]?\s*([A-Z0-9Α-Ω0-9]{10}-[A-Z0-9Α-Ω0-9]{3})', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # 2. Απευθείας αναζήτηση του μοτίβου ΑΔΑ (10 αλφαριθμητικά - 3 αλφαριθμητικά)
    fallback_match = re.search(r'\b([A-Z0-9Α-Ω0-9]{10}-[A-Z0-9Α-Ω0-9]{3})\b', text)
    if fallback_match:
        return fallback_match.group(1).strip()

    return None


def load_pdf_document(file_path: str | Path) -> Tuple[str, Dict[str, Any]]:
    """
    Ενοποιημένος Hybrid Loader:
    1. Ελέγχει αν το PDF είναι Digital ή Scanned μέσω Density Analysis.
    2. Digital -> Ανάγνωση μέσω pypdf + Normalization + ADA Annotations.
    3. Scanned -> Τοπικό OCR (Tesseract ell+eng) + Normalization + ADA Regex.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Το αρχείο δεν βρέθηκε: {path}")

    track, raw_text, page_images = analyze_pdf_density(path)

    metadata: Dict[str, Any] = {
        "file_name": path.name,
        "track": track,
    }

    if track == "scanned":
        engine = get_ocr_engine()
        print(f"[Loader] Το {path.name} είναι SCANNED. Εκτέλεση με Engine: {engine.__class__.__name__}...")
        ocr_text = engine.extract_text(page_images)
        clean_text = normalize_greek_text(ocr_text)
        ada_code = extract_ada_from_text(clean_text)
        total_pages = len(page_images)
    else:
        reader = PdfReader(str(path))
        clean_text = normalize_greek_text(raw_text)
        ada_code = extract_ada_from_annotations(reader) or extract_ada_from_text(clean_text)
        total_pages = len(reader.pages)

    metadata["total_pages"] = total_pages
    metadata["char_count"] = len(clean_text)
    metadata["ada"] = ada_code or "Δεν εντοπίστηκε"

    return clean_text, metadata