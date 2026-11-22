from src.evaluation.text_evidence_anchor import find_text_anchor


def test_find_text_anchor():
    text = (
        "Εγκρίνουμε την απευθείας ανάθεση "
        "στην εταιρία ΔΗΜΗΤΡΙΟΣ ΚΑΝΑΡΗΣ ΚΑΙ ΣΙΑ ΟΕ, "
        "ΑΦΜ: 801033798."
    )

    result = find_text_anchor(
        value="ΔΗΜΗΤΡΙΟΣ ΚΑΝΑΡΗΣ ΚΑΙ ΣΙΑ ΟΕ",
        source_text=text,
    )

    assert result is not None
    assert result["text"] == "ΔΗΜΗΤΡΙΟΣ ΚΑΝΑΡΗΣ ΚΑΙ ΣΙΑ ΟΕ"
    assert text[result["start"]:result["end"]] == result["text"]

def test_find_text_anchor_across_newline():
    text = (
        "Εγκρίνουμε την ανάθεση στην εταιρία "
        "ΔΗΜΗΤΡΙΟΣ ΚΑΝΑΡΗΣ ΚΑΙ ΣΙΑ\n"
        "ΟΕ, ΑΦΜ: 801033798"
    )

    result = find_text_anchor(
        value="ΔΗΜΗΤΡΙΟΣ ΚΑΝΑΡΗΣ ΚΑΙ ΣΙΑ ΟΕ",
        source_text=text,
    )

    assert result is not None

    assert result["text"] == (
        "ΔΗΜΗΤΡΙΟΣ ΚΑΝΑΡΗΣ ΚΑΙ ΣΙΑ\nΟΕ"
    )

    assert text[result["start"]:result["end"]] == result["text"]

def test_text_anchor_preserves_context():
    text = (
        "Εγκρίνουμε την ανάθεση στην εταιρία "
        "ΔΗΜΗΤΡΙΟΣ ΚΑΝΑΡΗΣ ΚΑΙ ΣΙΑ\n"
        "ΟΕ, ΑΦΜ: 801033798"
    )

    result = find_text_anchor(
        value="ΔΗΜΗΤΡΙΟΣ ΚΑΝΑΡΗΣ ΚΑΙ ΣΙΑ ΟΕ",
        source_text=text,
        context_chars=40,
    )

    assert result is not None
    assert "στην εταιρία" in result["context"]
    assert "ΑΦΜ: 801033798" in result["context"]
    assert text[result["start"]:result["end"]] == result["text"]