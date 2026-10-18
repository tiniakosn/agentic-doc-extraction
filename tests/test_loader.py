from pathlib import Path
from src.utils.pdf_loader import load_pdf_document

docs = ["data/raw/doc_1_digital.pdf", "data/raw/doc_2_digital.pdf", "data/raw/doc_3_digital.pdf"]

for doc_path_str in docs:
    p = Path(doc_path_str)
    if not p.exists():
        print(f"Παράλειψη: Το {p} δεν υπάρχει.")
        continue

    print(f"\n================ ΕΛΕΓΧΟΣ: {p.name} ================")
    text, meta = load_pdf_document(p)
    print(f"Σελίδες: {meta['total_pages']}")
    print(f"Χαρακτήρες: {meta['char_count']}")
    print(f"Εντοπισμένος ΑΔΑ: {meta['ada']}")
    
    # Έλεγχος αν αποκαταστάθηκαν βασικές λέξεις στο doc_2
    if "doc_2" in p.name:
        has_euro = "ευρώ" in text.lower()
        has_misthoma = "μισθώματος" in text.lower()
        print(f"Αποκατάσταση 'ευρώ': {'ΕΠΙΤΥΧΙΑ' if has_euro else 'ΑΠΟΤΥΧΙΑ'}")
        print(f"Αποκατάσταση 'μισθώματος': {'ΕΠΙΤΥΧΙΑ' if has_misthoma else 'ΑΠΟΤΥΧΙΑ'}")