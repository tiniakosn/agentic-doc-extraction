from src.evaluation.evidence_repair import repair_field_evidence


def test_text_evidence_proposal_preserves_review():
    source_text = (
        "Εγκρίνουμε την ανάθεση στην εταιρία "
        "ΔΗΜΗΤΡΙΟΣ ΚΑΝΑΡΗΣ ΚΑΙ ΣΙΑ\n"
        "ΟΕ, ΑΦΜ: 801033798"
    )

    extraction = {
        "contractor": {
            "status": "present",
            "value": "ΔΗΜΗΤΡΙΟΣ ΚΑΝΑΡΗΣ ΚΑΙ ΣΙΑ ΟΕ",
            "evidence": "Ανάθεση στην εταιρεία",
        }
    }

    verification = {
        "contractor": {
            "value_grounding": {"status": "supported"},
            "evidence_matching": {"status": "unsupported"},
            "source_references": [],
        }
    }

    decisions = {
        "contractor": {
            "final_action": "review",
            "reason": "Available evidence is insufficient",
        }
    }

    repairs = repair_field_evidence(
        extraction=extraction,
        verification=verification,
        final_decisions=decisions,
        source_text=source_text,
    )

    assert repairs["contractor"]["repair_method"] == "text_evidence_proposal"
    assert "στην εταιρία" in repairs["contractor"]["repaired_evidence"]
    assert "ΑΦΜ: 801033798" in repairs["contractor"]["repaired_evidence"]

    assert decisions["contractor"]["final_action"] == "review"
    assert extraction["contractor"]["value"] == "ΔΗΜΗΤΡΙΟΣ ΚΑΝΑΡΗΣ ΚΑΙ ΣΙΑ ΟΕ"