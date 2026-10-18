from typing import TypedDict, Optional, List, Dict, Any


class ExecutionMetrics(TypedDict, total=False):
    total_duration_sec: float
    extractor_time_sec: float
    validator_time_sec: float
    corrector_time_sec: float


class ExtractionState(TypedDict):
    """
    Η κοινή μνήμη (Agent State) του LangGraph State Machine.
    
    Όλα τα δεδομένα που χρειάζονται οι Extractor, Validator και Corrector Nodes
    βρίσκονται συγκεντρωμένα εδώ.
    """
    # 1. Είσοδος του pipeline
    document_text: str                     # Το κείμενο του εγγράφου προς επεξεργασία
    pdf_metadata: Dict[str, Any]           # Μεταδεδομένα (ΑΔΑ από Annots, όνομα αρχείου, σελίδες)

    # 2. Αποτέλεσμα εξαγωγής
    extracted_data: Optional[Dict[str, Any]] # Τα δεδομένα σε μορφή λεξικού

    # 3. Παρατηρήσεις επικύρωσης (Verbal Feedback για το Reflexion)
   
    validation_errors: List[str]           # Λίστα με σφάλματα επικύρωσης που εντόπισε ο Validator
    feedback_message: Optional[str]        # Το συγκεντρωτικό λεκτικό feedback προς το LLM

    # 4. Μετρητές και Έλεγχος Ροής (Guardrails)
    retry_count: int                       # Αριθμός επαναλήψεων διόρθωσης
    max_retries: int                       # Όριο επαναλήψεων (αποφυγή infinite loops)
    is_valid: bool                         # Ένδειξη αν τα δεδομένα πληρούν όλους τους κανόνες

    # Audit Trail & Observability
    audit_log: List[Dict[str, Any]]
    metrics: ExecutionMetrics