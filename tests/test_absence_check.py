from src.evaluation.absence_check import check_absence


def test_no_text_is_not_checkable():
    assert check_absence("contractor", "")["status"] == "not_checkable"


def test_recipient_cue_found():
    assert check_absence("recipient", "ΠΡΟΣ: Δήμο Αθηναίων")["status"] == "cues_found"


def test_contractor_absence_supported():
    result = check_absence("contractor", "Απόφαση έγκρισης δαπάνης μετακίνησης")
    assert result["status"] == "supported"


def test_contractor_cue_ignores_accents_and_case():
    result = check_absence("contractor", "Αναθέτουμε στην εταιρεία ΑΛΦΑ")
    assert result["status"] == "cues_found"


def test_valid_afm_is_cue():
    assert check_absence("contractor_tax_id", "ΑΦΜ 801033798")["status"] == "cues_found"


def test_mobile_number_is_not_afm_cue():
    result = check_absence("contractor_tax_id", "Τηλ. 6983905183")
    assert result["status"] == "supported"


def test_issuing_authority_absence_not_checkable():
    result = check_absence("issuing_authority", "κάποιο κείμενο")
    assert result["status"] == "not_checkable"