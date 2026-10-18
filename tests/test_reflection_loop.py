from src.graph import build_graph
from src.schemas.state import ExtractionState


def test_adversarial_document_reflection():
  app = build_graph()

  # Παραπλανητικό έγγραφο:
  # Αναφέρει δύο εταιρείες: την αναθέτουσα αρχή και τον πραγματικό ανάδοχο.
  # Έχει επίσης έναν αριθμό πρωτοκόλλου που μοιάζει με ΑΦΜ και το πραγματικό ΑΦΜ παρακάτω.
  tricky_text = """
    ΕΛΛΗΝΙΚΗ ΔΗΜΟΚΡΑΤΙΑ - ΥΠΟΥΡΓΕΙΟ ΨΗΦΙΑΚΗΣ ΔΙΑΚΥΒΕΡΝΗΣΗΣ
    Αριθμός Πρωτοκόλλου / Έγκρισης: 12345678 (8 ψηφία - προσοχή δεν είναι ΑΦΜ)
    
    Αντικείμενο: Ανάθεση έργου συντήρησης δικτυακών υποδομών.
    
    Η σύμβαση συνάπτεται μεταξύ του Υπουργείου και της εταιρείας 
    "Nexus Telecom Μ.Α.Ε.", η οποία εδρεύει στο Μαρούσι Αττικής, 
    με επίσημο Αριθμό Φορολογικού Μητρώου ΑΦΜ: 884422119.
    
    Οικονομικοί Όροι:
    - Καθαρή Αξία: 15.000,00 ευρώ
    - Συντελεστής ΦΠΑ: 24%
    - Συνολική Δαπάνη: 18.600,00 ευρώ (15000 + 3600 ΦΠΑ)
    """

  initial_state = ExtractionState(document_text=tricky_text)

  print("\n--- Δοκιμή Σεναρίου με Παραπλανητικό Έγγραφο ---")
  final_output = app.invoke(initial_state)

  print("\n--- ΤΕΛΙΚΗ ΚΑΤΑΣΤΑΣΗ ---")
  print(f"Εγκυρότητα (is_valid): {final_output['is_valid']}")
  print(f"Αριθμός Προσπαθειών/Retries: {final_output['retry_count']}")
  print(f"Σφάλματα που έμειναν: {final_output['validation_errors']}")
  print("Τελικά Δεδομένα:")
  print(final_output["extracted_data"].model_dump_json(indent=2))

  assert final_output["is_valid"] is True
  assert final_output["extracted_data"].contractor_name == "Nexus Telecom Μ.Α.Ε."
  assert final_output["extracted_data"].tax_id == "884422119"
  print("\nΤο σύστημα ξεπέρασε τις παγίδες και εξήγαγε τα σωστά στοιχεία!")


if __name__ == "__main__":
  test_adversarial_document_reflection()