import sqlite3
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from src.schemas.state import ExtractionState
from src.nodes.extractor import extractor_node
from src.nodes.validator import validate_extraction
from src.nodes.corrector import corrector_node


def route_after_validation(state: ExtractionState) -> Literal["corrector", "__end__"]:
    """
    Δρομολογητής (Conditional Router).
    
    Ελέγχει αν το αποτέλεσμα είναι έγκυρο ή αν εξαντλήθηκαν τα περιθώρια διόρθωσης.
    """
    is_valid = state.get("is_valid", False)
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    if is_valid:
        return END

    if retry_count >= max_retries:
        print(f"[Graph Router] Εξαντλήθηκαν οι προσπάθειες διόρθωσης ({retry_count}/{max_retries}).")
        return END

    return "corrector"


def build_graph(checkpointer=None):
    """
    Κατασκευάζει και μεταγλωττίζει τον γράφο ροής του πράκτορα.
    """
    workflow = StateGraph(ExtractionState)

    # 1. Προσθήκη Κόμβων
    workflow.add_node("extractor", extractor_node)
    workflow.add_node("validator", validate_extraction)
    workflow.add_node("corrector", corrector_node)

    # 2. Σύνδεση Ακμών (Edges)
    workflow.add_edge(START, "extractor")
    workflow.add_edge("extractor", "validator")

    # 3. Υπό Συνθήκη Μετάβαση μετά τον Validator
    workflow.add_conditional_edges(
        "validator",
        route_after_validation,
        {
            "corrector": "corrector",
            END: END,
        }
    )

    # 4. Επιστροφή από τον Corrector πίσω στον Validator (Reflexion Cycle)
    workflow.add_edge("corrector", "validator")

    return workflow.compile(checkpointer=checkpointer)


# Default shared DB connection for local execution
DB_PATH = "evaluation_results/checkpoints.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
memory_saver = SqliteSaver(conn)

# Μεταγλωττισμένο εκτελέσιμο γράφημα με Persistent Memory
app = build_graph(checkpointer=memory_saver)