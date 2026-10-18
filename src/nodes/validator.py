import re
import unicodedata
from typing import Dict, Any, List
from pydantic import ValidationError

from src.schemas.state import ExtractionState
from src.schemas.contract import ContractSchema

import time


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
    start_time = time.time()
    errors: List[str] = []
    raw_data = state.get("extracted_data")
    document_text = state.get("document_text", "")
    audit_log = list(state.get("audit_log", []))
    metrics = dict(state.get("metrics", {}))

    # 1. Έλεγχος ύπαρξης εξαχθέντων δεδομένων
    if not raw_data:
        errors.append("Δεν παρήχθησαν εξαγόμενα δεδομένα από τον Extractor (None).")
        elapsed = round(time.time() - start_time, 3)
        audit_log.append({
            "node": "validator",
            "is_valid": False,
            "errors_count": len(errors),
            "elapsed_sec": elapsed,
        })
        return {
            "validation_errors": errors,
            "feedback_message": "Η προηγούμενη εξαγωγή απέτυχε πλήρως.",
            "is_valid": False,
            "audit_log": audit_log,
        }

    # 2. Schema & Deterministic Constraints (Pydantic / Modulo 11 / Math)
    try:
        ContractSchema(**raw_data)
    except ValidationError as e:
        for err in e.errors():
            field_name = " -> ".join([str(loc) for loc in err["loc"]])
            errors.append(f"Σφάλμα πεδίου '{field_name}': {err['msg']}")

    # 3. Grounding Verification
    norm_doc = strip_accents_and_clean(document_text)

    # Έλεγχος ΑΦΜ: Ελέγχουμε ΜΟΝΟ αν υπάρχει πραγματική τιμή και δεν είναι None / κενό
    tax_id = raw_data.get("tax_id")
    if tax_id is not None:
        tax_str = str(tax_id).strip()
        if tax_str and tax_str.lower() != "none" and tax_str != "000000000":
            clean_digits = re.sub(r'\D', '', tax_str)
            raw_doc_digits = re.sub(r'\D', '', document_text)
            if clean_digits and clean_digits not in raw_doc_digits:
                errors.append(
                    f"Grounding Error: Το ΑΦΜ '{tax_str}' δεν εντοπίστηκε στο αρχικό κείμενο του εγγράφου."
                )

    # Έλεγχος Αναδόχου (Token-level Inclusion)
    
    contractor = raw_data.get("contractor_name")
    if contractor and "ΑΝΕΥ" not in contractor.upper():
        norm_contractor_tokens = strip_accents_and_clean(contractor).split()
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

    elapsed = round(time.time() - start_time, 3)
    metrics["validator_time_sec"] = metrics.get("validator_time_sec", 0) + elapsed

    audit_log.append({
        "node": "validator",
        "is_valid": is_valid,
        "errors_count": len(errors),
        "elapsed_sec": elapsed,
    })

    return {
        "validation_errors": errors,
        "feedback_message": feedback_message,
        "is_valid": is_valid,
        "audit_log": audit_log,
        "metrics": metrics,
    }