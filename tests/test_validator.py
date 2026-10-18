from src.nodes.validator import validate_extraction
from src.schemas.state import ExtractionState

def test_validator_node():
    mock_doc = "ΑΠΟΦΑΣΗ ΑΝΑΘΕΣΗΣ στον ανάδοχο ΚΛΕΙΘΡΟΠΟΙΟΣ ΜΠΟΥΛΙΟΣ ΧΡ. ΓΙΑΝΝΑΚΗΣ με ΑΦΜ 079242023 ποσού 322.34 ευρώ πλέον ΦΠΑ 24% σύνολο 399.90 ευρώ."

    # Σενάριο 1: Έγκυρη εξαγωγή
    valid_state: ExtractionState = {
        "document_text": mock_doc,
        "pdf_metadata": {},
        "extracted_data": {
            "document_title": "ΑΠΟΦΑΣΗ ΑΝΑΘΕΣΗΣ",
            "contractor_name": "ΚΛΕΙΘΡΟΠΟΙΟΣ ΜΠΟΥΛΙΟΣ ΧΡ. ΓΙΑΝΝΑΚΗΣ",
            "tax_id": "079242023",
            "financials": {
                "net_amount": 322.34,
                "vat_rate": 0.24,
                "total_amount": 399.90,
            }
        },
        "validation_errors": [],
        "feedback_message": None,
        "retry_count": 0,
        "max_retries": 3,
        "is_valid": False,
    }

    res_valid = validate_extraction(valid_state)
    assert res_valid["is_valid"] is True, f"Αποτυχία στο έγκυρο σενάριο: {res_valid['validation_errors']}"
    print("Σενάριο 1 (Έγκυρο): ΠΕΡΑΣΕ ΕΠΙΤΥΧΩΣ")

    # Σενάριο 2: Άκυρο ΑΦΜ (Modulo 11 failure) + Hallucinated Contractor
    invalid_state: ExtractionState = {
        "document_text": mock_doc,
        "pdf_metadata": {},
        "extracted_data": {
            "document_title": "ΑΠΟΦΑΣΗ ΑΝΑΘΕΣΗΣ",
            "contractor_name": "ΑΝΥΠΑΡΚΤΗ ΕΤΑΙΡΕΙΑ Α.Ε.",
            "tax_id": "079242024",  # Άκυρο check digit
            "financials": {
                "net_amount": 322.34,
                "vat_rate": 0.24,
                "total_amount": 399.90,
            }
        },
        "validation_errors": [],
        "feedback_message": None,
        "retry_count": 0,
        "max_retries": 3,
        "is_valid": False,
    }

    res_invalid = validate_extraction(invalid_state)
    assert res_invalid["is_valid"] is False
    assert len(res_invalid["validation_errors"]) >= 2
    print("Σενάριο 2 (Σφάλματα Modulo 11 & Grounding): ΕΝΤΟΠΙΣΤΗΚΑΝ ΣΩΣΤΑ")
    print("\nΠαράδειγμα Feedback Message για το Reflexion:")
    print(res_invalid["feedback_message"])

if __name__ == "__main__":
    test_validator_node()