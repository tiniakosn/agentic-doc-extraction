import re
import unicodedata
from typing import Dict, Any, List
from pydantic import ValidationError

from src.schemas.state import ExtractionState
from src.schemas.contract import ContractSchema


def strip_accents_and_clean(s: str) -> str:
    """
    Αφαιρεί τόνους, σημεία στίξης και περιττά κενά για ανθεκτική σύγκριση (Fuzzy/Clean Grounding).
    """
    if not s:
        return ""
    # Απομάκρυνση τόνων
    nfkd_form = unicodedata.normalize('NFKD', s)
    no_accents = ''.join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Κανονικοποίηση σε πεζά και αφαίρεση ειδικών συμβόλων
    cleaned = re.sub(r'[^\w\s]', ' ', no_accents.lower())
    return " ".join(cleaned.split())


def validate_extraction(state: ExtractionState) -> Dict[str, Any]:
    """
    Validator Node (Symbolic Verification Layer).
    
    Ελέγχει:
    1. Ύπαρξη και εγκυρότητα Pydantic Schema (Modulo 11, θετικά ποσά).
    2. Text Grounding: Παρουσία ΑΦΜ και αναδόχου στο κείμενο.
    3. Οικονομική συνέπεια (Net + VAT == Total).
    
    Επιστρέφει partial update για το State:
    - is_valid: bool
    - validation_errors: List[str]
    - feedback_message: Optional[str]
    """
    errors: List[str] = []
    raw_data = state.get("extracted_data")
    document_text = state.get("document_text", "")

    # 1. Έλεγχος ύπαρξης εξαχθέντων δεδομένων
    if not raw_data:
        errors.append("Δεν παρήχθησαν εξαγόμενα δεδομένα από τον Extractor (None).")
        return {
            "validation_errors": errors,
            "feedback_message": "Η προηγούμενη εξαγωγή απέτυχε πλήρως. Εξήγαγε ξανά τα στοιχεία από το κείμενο.",
            "is_valid": False,
        }

    # 2. Schema & Deterministic Constraints (Pydantic / Modulo 11 / Math)
    validated_contract = None
    try:
        validated_contract = ContractSchema(**raw_data)
    except ValidationError as e:
        for err in e.errors():
            field_name = " -> ".join([str(loc) for loc in err["loc"]])
            msg = err["msg"]
            errors.append(f"Σφάλμα πεδίου '{field_name}': {msg}")

    # 3. Grounding Verification (Έλεγχος Τεκμηρίωσης στο Κείμενο)
    norm_doc = strip_accents_and_clean(document_text)

    # Έλεγχος ΑΦΜ: Αφαιρούμε κενά και αναζητούμε το 9ψήφιο string
    tax_id = str(raw_data.get("tax_id", "")).strip()
    if tax_id:
        if tax_id not in re.sub(r'\s+', '', document_text):
            errors.append(
                f"Grounding Error: Το ΑΦΜ '{tax_id}' δεν εντοπίστηκε αυτούσιο στο αρχικό κείμενο του εγγράφου."
            )

    # Έλεγχος Αναδόχου (Token-level Inclusion)
    contractor = raw_data.get("contractor_name", "")
    if contractor and contractor.upper() != "ΑΝΕΥ ΑΝΑΔΟΧΟΥ":
        norm_contractor_tokens = strip_accents_and_clean(contractor).split()
        # Ελέγχουμε αν τουλάχιστον τα περισσότερα tokens του αναδόχου υπάρχουν στο έγγραφο
        missing_tokens = [t for t in norm_contractor_tokens if t not in norm_doc]
        if len(missing_tokens) > len(norm_contractor_tokens) // 2:
            errors.append(
                f"Grounding Error: Η επωνυμία αναδόχου '{contractor}' δεν επιβεβαιώνεται επαρκώς από το πρωτότυπο κείμενο."
            )

    # 4. Σύνθεση Ανατροφοδότησης (Feedback Message για τον Corrector)
    is_valid = len(errors) == 0
    feedback_message = None

    if not is_valid:
        formatted_list = "\n".join([f"- {err}" for err in errors])
        feedback_message = (
            f"Εντοπίστηκαν τα ακόλουθα {len(errors)} σφάλματα κατά τον συμβολικό έλεγχο:\n"
            f"{formatted_list}\n"
            f"Παρακαλώ διόρθωσε τα συγκεκριμένα πεδία ανατρέχοντας ξανά στο πρωτότυπο κείμενο."
        )

    return {
        "validation_errors": errors,
        "feedback_message": feedback_message,
        "is_valid": is_valid,
    }