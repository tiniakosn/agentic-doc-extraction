from src.graph import build_graph
from src.schemas.contract import ContractSchema, FinancialTerms
from src.schemas.state import ExtractionState


def test_forced_reflection_execution():
  app = build_graph()

  # Έγγραφο όπου το κείμενο αναφέρει δύο αναδόχους:
  # μία αρχική ανάθεση σε μια εταιρεία και τελική υποκατάσταση σε άλλη.
  text = """
    ΣΥΜΒΑΣΗ ΤΡΟΠΟΠΟΙΗΣΗΣ
    Αρχικός ανάδοχος ήταν η επιχείρηση "Alpha Beta E.E." (ΑΦΜ 111111111).
    Δυνάμει της παρούσας, η σύμβαση εκχωρείται οριστικά και αμετάκλητα 
    στον νέο ανάδοχο "Omega Cybernetics A.E." με ΑΦΜ 999999999.
    
    Οικονομικοί όροι:
    Καθαρό ποσό: 8.000,00 ευρώ
    ΦΠΑ 24%: 1.920,00 ευρώ
    Συνολικό ποσό: 9.920,00 ευρώ
    """

  initial_state = ExtractionState(document_text=text)

  print("\n--- Εκτέλεση Τεστ Αυτοδιόρθωσης ---")
  final_output = app.invoke(initial_state)

  print("\n--- ΤΕΛΙΚΟ ΑΠΟΤΕΛΕΣΜΑ ---")
  print(f"is_valid: {final_output['is_valid']}")
  print(f"Συνολικά Retries: {final_output['retry_count']}")
  print("Ανάδοχος:", final_output["extracted_data"].contractor_name)
  print("ΑΦΜ:", final_output["extracted_data"].tax_id)


if __name__ == "__main__":
  test_forced_reflection_execution()