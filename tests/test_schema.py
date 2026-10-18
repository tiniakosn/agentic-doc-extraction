
from pydantic import ValidationError
from src.schemas.contract import ContractSchema, FinancialTerms

def test_valid_contract():
    data = {
        "document_title": "Απόφαση Ανάθεσης",
        "contractor_name": "ΜΠΟΥΛΙΟΣ ΧΡ. ΓΙΑΝΝΑΚΗΣ",
        "tax_id": "079242023",  # Έγκυρο Modulo 11 ΑΦΜ
        "financials": {
            "net_amount": 322.50,
            "vat_rate": 0.24,
            "total_amount": 399.90,
        }
    }
    contract = ContractSchema(**data)
    assert contract.tax_id == "079242023"
    print("Έγκυρο contract πέρασε επιτυχώς!")

def test_invalid_afm_fails():
    data = {
        "document_title": "Απόφαση Ανάθεσης",
        "contractor_name": "ΤΕΣΤ",
        "tax_id": "079242024",  # Λάθος check digit
        "financials": {
            "net_amount": 100.0,
            "vat_rate": 0.24,
            "total_amount": 124.0,
        }
    }
    try:
        ContractSchema(**data)
        assert False, "Έπρεπε να πετάξει ValidationError για το ΑΦΜ!"
    except ValidationError:
        print("Το άκυρο ΑΦΜ απορρίφθηκε σωστά από το Schema!")

if __name__ == "__main__":
    test_valid_contract()
    test_invalid_afm_fails()