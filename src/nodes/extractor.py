import os
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from src.schemas.state import ExtractionState
from src.schemas.contract import ContractSchema
from src.utils.text_pruner import prune_document_for_llm

import time

load_dotenv()


def get_llm(model_name: str = "openai/gpt-oss-120b"):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Το GROQ_API_KEY δεν βρέθηκε στο αρχείο .env.")
    
    return ChatGroq(
        model_name=model_name,
        temperature=0.0,
    )


EXTRACTION_SYSTEM_PROMPT = """Είσαι εξειδικευμένος αναλυτής ελληνικών δημοσίων εγγράφων (πρόγραμμα Διαύγεια).
Αποστολή σου είναι να εξάγεις με πιστότητα τα στοιχεία του εγγράφου (σύμβαση, ανάθεση ή πρόσκληση εκδήλωσης ενδιαφέροντος).

Κανόνες:
1. document_title: Ο πλήρης τίτλος/θέμα του εγγράφου.
2. contractor_name: Η επωνυμία του αναδόχου. Αν πρόκειται για διακήρυξη/πρόσκληση και ΔΕΝ υπάρχει ανάδοχος, βάλε 'ΑΝΕΥ ΑΝΑΔΟΧΟΥ'.
3. tax_id: Το 9ψήφιο ΑΦΜ του αναδόχου. Αν δεν υπάρχει ανάδοχος ή είναι πρόσκληση, βάλε null.
4. financials:
   - net_amount: Το καθαρό ποσό προ ΦΠΑ.
   - vat_rate: Ο συντελεστής ΦΠΑ (π.χ. 0.24).
   - total_amount: Το συνολικό ποσό με ΦΠΑ.
   - Βεβαιώσου ότι: total_amount = round(net_amount * (1 + vat_rate), 2)."""


def extractor_node(state: ExtractionState) -> Dict[str, Any]:
    start_time = time.time()

    raw_text = state["document_text"]
    metadata = state.get("pdf_metadata", {})
    ada = metadata.get("ada", "Δεν εντοπίστηκε")
    audit_log = list(state.get("audit_log", []))
    metrics = dict(state.get("metrics", {}))

    clean_text = prune_document_for_llm(raw_text, max_chars=7000)

    prompt = ChatPromptTemplate.from_messages([
        ("system", EXTRACTION_SYSTEM_PROMPT),
        ("human", "Μεταδεδομένα Εγγράφου: ΑΔΑ = {ada}\n\nΚείμενο Εγγράφου:\n{text}")
    ])

    extracted_dict = None
    used_model = None

    for target_model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]:
        try:
            llm = get_llm(model_name=target_model)
            # Χρησιμοποιούμε json schema extraction ώστε να λαμβάνουμε το dict
            structured_llm = llm.with_structured_output(ContractSchema)
            chain = prompt | structured_llm
            result = chain.invoke({"ada": ada, "text": clean_text})
            
            if isinstance(result, ContractSchema):
                extracted_dict = result.model_dump()
            elif isinstance(result, dict):
                extracted_dict = result
            used_model = target_model
            break
        except Exception as e:
            # Αν αποτύχει το parsing του Pydantic κατά την έξοδο, δοκιμάζουμε να ανακτήσουμε
            # τα raw arguments αν υπάρχουν, αλλιώς πάμε στο επόμενο
            err_msg = str(e)
            print(f"[Extractor Debug] {target_model}: {err_msg[:120]}...")
            continue

    elapsed = round(time.time() - start_time, 2)
    metrics["extractor_time_sec"] = elapsed

    audit_log.append({
        "node": "extractor",
        "model_used": used_model,
        "elapsed_sec": elapsed,
        "extracted_summary": extracted_dict.get("contractor_name") if extracted_dict else None,
    })

    return {
        "extracted_data": extracted_dict,
        "is_valid": False,
        "audit_log": audit_log,
        "metrics": metrics,
    }