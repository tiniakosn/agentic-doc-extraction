import re

def prune_document_for_llm(text: str, max_chars: int = 7500) -> str:
    """
    Αν το έγγραφο είναι μικρότερο από max_chars, το επιστρέφει ως έχει.
    Αν είναι μεγαλύτερο, διατηρεί την αρχή (Θέμα/Στοιχεία) και το τέλος
    όπου συνήθως βρίσκεται το αποφασιστικό μέρος (Αποφασίζουμε / Αναθέτουμε).
    """
    if len(text) <= max_chars:
        return text

    # Εντοπισμός έναρξης αποφασιστικού μέρους αν υπάρχει
    decision_match = re.search(r'(Α\s*Π\s*Ο\s*Φ\s*Α\s*Σ\s*Ι\s*Ζ\s*Ο\s*Υ\s*Μ\s*Ε|Δ\s*Ι\s*Α\s*Κ\s*Η\s*Ρ\s*Υ\s*Σ\s*Σ\s*Ο\s*Υ\s*Μ\s*Ε|Π\s*Ρ\s*Ο\s*Σ\s*Κ\s*Α\s*Λ\s*Ο\s*Υ\s*Μ\s*Ε)', text, re.IGNORECASE)
    
    half_budget = max_chars // 2

    head = text[:half_budget]
    
    if decision_match and decision_match.start() > half_budget:
        # Παίρνουμε από το σημείο της απόφασης και μετά
        tail_start = decision_match.start()
        tail = text[tail_start : tail_start + half_budget]
    else:
        # Παίρνουμε απλώς το τελευταίο κομμάτι του εγγράφου
        tail = text[-half_budget:]

    return f"{head}\n\n[... ΠΑΡΑΛΕΙΨΗ ΕΝΔΙΑΜΕΣΩΝ ΝΟΜΙΚΩΝ ΔΙΑΤΑΞΕΩΝ ...]\n\n{tail}"