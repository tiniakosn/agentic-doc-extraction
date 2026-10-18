from langgraph.graph import StateGraph, START, END
from src.schemas.state import ExtractionState
from src.schemas.contract import ContractSchema, FinancialTerms
from src.nodes.extractor import extract_contract
from src.nodes.validator import validate_extraction
from src.nodes.corrector import correct_extraction
from src.graph import should_continue

def mock_flawed_extractor_first_pass(state: ExtractionState):
    """
    Προσομοιωτής Extractor:
    - Στον γύρο 0 (πρώτη προσπάθεια): Επιστρέφει σκόπιμα λάθος ΑΦΜ (Ghost AFM).
    - Στον γύρο 1 (μετά το Corrector feedback): Καλεί το πραγματικό Gemini API για να διορθώσει.
    """
    if state.retry_count == 0:
        print("\n[MOCK EXTRACTOR - ΠΡΟΣΠΑΘΕΙΑ 1]: Παράγει σκόπιμα λανθασμένο ΑΦΜ...")
        flawed_data = ContractSchema(
            document_title="Σύμβαση Συντήρησης Δικτύων",
            contractor_name="Omega Cybernetics A.E.",
            tax_id="000000000",  # Αυτό το ΑΦΜ ΔΕΝ υπάρχει στο κείμενο -> Hallucination!
            financials=FinancialTerms(
                net_amount=8000.0,
                vat_rate=0.24,
                total_amount=9920.0
            )
        )
        return {"extracted_data": flawed_data}
    else:
        print(f"\n[REAL GEMINI EXTRACTOR - ΠΡΟΣΠΑΘΕΙΑ {state.retry_count + 1}]: Διαβάζει το feedback και διορθώνει...")
        return extract_contract(state)

def test_full_agentic_recovery():
    # Στήνουμε ένα test graph με τον mock extractor
    builder = StateGraph(ExtractionState)
    builder.add_node("extractor", mock_flawed_extractor_first_pass)
    builder.add_node("validator", validate_extraction)
    builder.add_node("corrector", correct_extraction)

    builder.add_edge(START, "extractor")
    builder.add_edge("extractor", "validator")
    builder.add_conditional_edges(
        "validator",
        should_continue,
        {
            "valid": END,
            "max_retries": END,
            "retry": "corrector"
        }
    )
    builder.add_edge("corrector", "extractor")
    app = builder.compile()

    contract_text = """
    ΣΥΜΒΑΣΗ ΣΥΝΤΗΡΗΣΗΣ ΔΙΚΤΥΩΝ
    Ανάδοχος: Omega Cybernetics A.E.
    Επίσημο ΑΦΜ: 999999999
    
    Οικονομικό Αντικείμενο:
    Καθαρό Ποσό: 8.000,00 ευρώ
    ΦΠΑ 24%: 1.920,00 ευρώ
    Σύνολο: 9.920,00 ευρώ
    """

    initial_state = ExtractionState(document_text=contract_text)
    
    print("\n================== ΕΝΑΡΞΗ AGENTIC RECOVERY DEMO ==================")
    final_output = app.invoke(initial_state)
    print("==================================================================")

    print("\n--- ΤΕΛΙΚΑ ΑΠΟΤΕΛΕΣΜΑΤΑ ---")
    print(f"Εγκυρότητα (is_valid): {final_output['is_valid']}")
    print(f"Τελικός αριθμός Retries: {final_output['retry_count']}")
    print(f"Τελικό ΑΦΜ: {final_output['extracted_data'].tax_id}")
    
    assert final_output['is_valid'] is True
    assert final_output['retry_count'] == 1
    assert final_output['extracted_data'].tax_id == "999999999"
    print("\nΕΠΙΤΥΧΙΑ: Ο γράφος εντόπισε το hallucination, κάλεσε τον Corrector και το LLM ανέκαμψε πλήρως!")

if __name__ == "__main__":
    test_full_agentic_recovery()