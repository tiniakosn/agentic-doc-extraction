from src.evaluation.evidence_verifier import morphological_match


def test_genitive_matches_nominative():
    assert morphological_match(
        "Βιοτεχνικό Επιμελητήριο Θεσσαλονίκης",
        "Εξόδων 2026 του Βιοτεχνικού Επιμελητηρίου Θεσσαλονίκης",
    )


def test_short_names_inflect():
    assert morphological_match("Δήμος Σάμου", "αποφασίζει ο Δήμου Σάμου")


def test_different_entity_does_not_match():
    assert not morphological_match("Δήμος Λήμνου", "του Δήμου Σάμου")


def test_numbers_must_match_exactly():
    assert not morphological_match("801033798", "ΑΦΜ 801033799")
    assert morphological_match("801033798", "ΑΦΜ 801033798")