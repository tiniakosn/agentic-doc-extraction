from src.graph import build_graph
from src.schemas.state import ExtractionState
from src.schemas.contract import ContractSchema, FinancialTerms


def test_graph_loop_and_circuit_breaker():
    app = build_graph()

    # Έγγραφο και λανθασμένα δεδομένα που θα προκαλούν πάντα σφάλμα στο validation
    initial_state = ExtractionState(
        document_text="Σύμβαση με την εταιρεία Alpha Solutions.",
        extracted_data=ContractSchema(
            document_title="Σύμβαση",
            contractor_name="Ghost Company",  # Δεν υπάρχει στο κείμενο!
            tax_id="123456789",
            financials=FinancialTerms(
                net_amount=100.0,
                vat_rate=0.24,
                total_amount=124.0,
            ),
        ),
    )

    print("\n--- Εκτέλεση LangGraph State Machine ---")
    final_state = app.invoke(initial_state)

    print(f"Τελικό is_valid: {final_state['is_valid']}")
    print(f"Τελικό retry_count: {final_state['retry_count']}")
    print(f"Εντοπισμένα σφάλματα: {final_state['validation_errors']}")

    # Βεβαιωνόμαστε ότι το σύστημα δεν κόλλησε σε infinite loop
    assert final_state["is_valid"] is False
    assert final_state["retry_count"] == 3
    print("\nΟ γράφος εκτέλεσε επιτυχώς 3 κύκλους και τερμάτισε βάσει circuit breaker!")


if __name__ == "__main__":
    test_graph_loop_and_circuit_breaker()