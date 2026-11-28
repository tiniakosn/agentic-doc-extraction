"""Build verification feedback for reflection-based re-extraction."""

FIELD_HINTS = {
    "contractor_tax_id": (
        "Ο ΑΦΜ είναι ακριβώς 9 ψηφία· μην τον συγχέεις με τηλέφωνο "
        "ή αριθμό πρωτοκόλλου."
    ),
    "contractor": (
        "Ανάδοχος είναι μόνο όποιος ρητά αναλαμβάνει ανάθεση ή σύμβαση."
    ),
}


def build_correction_feedback(
    extraction: dict,
    final_decisions: dict,
) -> str | None:
    """Describe rejected fields so the model can correct them."""

    lines = []

    for field_name, decision in final_decisions.items():
        if decision.get("final_action") != "reprocess":
            continue

        value = (extraction.get(field_name) or {}).get("value")
        reason = decision.get("reason", "Verification failed")

        line = f"- {field_name}: η τιμή «{value}» απορρίφθηκε. Λόγος: {reason}."

        hint = FIELD_HINTS.get(field_name)
        if hint:
            line += f" {hint}"

        lines.append(line)

    if not lines:
        return None

    return (
        "Στην προηγούμενη προσπάθεια εντοπίστηκαν τα εξής προβλήματα:\n"
        + "\n".join(lines)
        + "\nΞαναέλεγξε προσεκτικά αυτά τα πεδία στο κείμενο. "
        "Αν η σωστή τιμή δεν υπάρχει, δήλωσε not_present ή uncertain. "
        "Μην επαναλάβεις τιμές που απορρίφθηκαν."
    )