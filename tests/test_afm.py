from src.evaluation.field_validation import validate_greek_afm

def test_afm_validation():
    # 1. Πραγματικό ΑΦΜ από το doc_1
    real_afm = "079242023"
    assert validate_greek_afm(real_afm) is True, f"Το πραγματικό ΑΦΜ {real_afm} απέτυχε!"

    # 2. Παραποιημένο ΑΦΜ (λάθος check digit)
    fake_afm = "079242024"
    assert validate_greek_afm(fake_afm) is False, f"Το παραποιημένο ΑΦΜ {fake_afm} έγινε δεκτό εσφαλμένα!"

    # 3. Λάθος πλήθος ψηφίων
    invalid_len = "12345678"
    assert validate_greek_afm(invalid_len) is False

    print("Όλοι οι έλεγχοι Modulo 11 πέρασαν με απόλυτη επιτυχία!")

def test_afm_rejects_mobile_phone():
    assert validate_greek_afm("6983905183") is False


def test_afm_rejects_missing_value():
    assert validate_greek_afm(None) is False

if __name__ == "__main__":
    test_afm_validation()