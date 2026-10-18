import json
from pathlib import Path
from src.utils.pdf_loader import load_pdf_document
from src.nodes.extractor import extractor_node
from src.schemas.state import ExtractionState

def run_live_test():
    doc_path = Path("data/raw/doc_1_digital.pdf")
    if not doc_path.exists():
        print(f"Σφάλμα: Το αρχείο {doc_path} δεν βρέθηκε.")
        return

    print("1. Φόρτωση και κανονικοποίηση εγγράφου...")
    text, metadata = load_pdf_document(doc_path)
    print(f"   ΑΔΑ: {metadata.get('ada')}")
    print(f"   Χαρακτήρες: {len(text)}")

    print("\n2. Αρχικοποίηση Agent State...")
    state: ExtractionState = {
        "document_text": text,
        "pdf_metadata": metadata,
        "extracted_data": None,
        "validation_errors": [],
        "feedback_message": None,
        "retry_count": 0,
        "max_retries": 3,
        "is_valid": False,
    }

    print("\n3. Εκτέλεση Extractor Node (κλήση Groq LLM)...")
    update = extractor_node(state)
    
    extracted = update.get("extracted_data")
    print("\n================ ΑΠΟΤΕΛΕΣΜΑ ΕΞΑΓΩΓΗΣ ================")
    if extracted:
        print(json.dumps(extracted, ensure_ascii=False, indent=2))
    else:
        print("ΑΠΟΤΥΧΙΑ: Ο extractor επέστρεψε None.")

if __name__ == "__main__":
    run_live_test()