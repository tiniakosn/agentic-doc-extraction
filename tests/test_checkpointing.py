from pathlib import Path
from src.graph import app
from src.utils.pdf_loader import load_pdf_document
from src.schemas.state import ExtractionState


def test_checkpoint_persistence():
    doc_path = Path("data/raw/doc_1_digital.pdf")
    text, metadata = load_pdf_document(doc_path)
    ada = metadata.get("ada", "TEST-ADA-001")

    # Κάθε εκτέλεση έχει μοναδικό thread_id βάσει ΑΔΑ
    config = {"configurable": {"thread_id": ada}}

    initial_state: ExtractionState = {
        "document_text": text,
        "pdf_metadata": metadata,
        "extracted_data": None,
        "validation_errors": [],
        "feedback_message": None,
        "retry_count": 0,
        "max_retries": 3,
        "is_valid": False,
        "audit_log": [],
        "metrics": {},
    }

    print(f"\n>>> 1. Εκτέλεση Pipeline με thread_id: {ada}")
    final_state = app.invoke(initial_state, config=config)
    print(f"    Αποτέλεσμα is_valid: {final_state.get('is_valid')}")

    print("\n>>> 2. Ανάκτηση Κατάστασης από τη Βάση (State Inspection)...")
    saved_snapshot = app.get_state(config)
    print(f"    Τελευταίος Κόμβος που εκτελέστηκε: {saved_snapshot.next}")
    print(f"    Αποθηκευμένο Contractor Name: {saved_snapshot.values.get('extracted_data', {}).get('contractor_name')}")
    print(f"    Βήματα στο ιστορικό: {len(list(app.get_state_history(config)))}")

    assert saved_snapshot.values.get("is_valid") is True
    print("\n[OK] Το Checkpointing λειτουργεί πλήρως και αποθηκεύτηκε στη βάση!")


if __name__ == "__main__":
    test_checkpoint_persistence()