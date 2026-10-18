import json
import re
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from src.nodes.extractor import get_llm
from src.schemas.contract import ContractSchema
from src.schemas.state import ExtractionState
from src.utils.text_pruner import prune_document_for_llm

import time

CORRECTOR_SYSTEM_PROMPT = """Είσαι εξειδικευμένος ελεγκτής και διορθωτής δεδομένων ελληνικών δημοσίων εγγράφων (Διαύγεια).
Αποστολή σου είναι να διορθώσεις τα σφάλματα που εντόπισε ο Validator.

Οδηγίες:
1. Αν το έγγραφο είναι πρόσκληση ενδιαφέροντος / προκήρυξη χωρίς ανάδοχο, δήλωσε contractor_name: 'ΑΝΕΥ ΑΝΑΔΟΧΟΥ' και tax_id: null.
2. Επαλήθευσε τα ποσά: total_amount = round(net_amount * (1 + vat_rate), 2).
3. Κάλεσε υποχρεωτικά το εργαλείο ContractSchema."""


def extract_json_fallback(text: str) -> Dict[str, Any]:
    """Εξάγει JSON λεξικό αν το μοντέλο απαντήσει με markdown αντί για function call."""
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    return {}


def corrector_node(state: ExtractionState) -> Dict[str, Any]:
    start_time = time.time()

    raw_text = state["document_text"]
    metadata = state.get("pdf_metadata", {})
    ada = metadata.get("ada", "Δεν εντοπίστηκε")
    current_extracted = state.get("extracted_data") or {}
    feedback = state.get("feedback_message", "Δεν δόθηκε μήνυμα λάθους.")
    retries = state.get("retry_count", 0)
    audit_log = list(state.get("audit_log", []))
    metrics = dict(state.get("metrics", {}))

    clean_text = prune_document_for_llm(raw_text, max_chars=7000)

    prompt = ChatPromptTemplate.from_messages([
        ("system", CORRECTOR_SYSTEM_PROMPT),
        (
            "human",
            "Πρωτότυπο Κείμενο (ΑΔΑ: {ada}):\n{text}\n\n"
            "Προηγούμενη Εξαγωγή:\n{previous_output}\n\n"
            "Σφάλματα προς διόρθωση:\n{feedback}\n\n"
            "Διόρθωσε τα δεδομένα.",
        ),
    ])

    corrected_dict = current_extracted
    used_model = None

    for target_model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]:
        try:
            llm = get_llm(model_name=target_model)
            structured_llm = llm.with_structured_output(ContractSchema)
            chain = prompt | structured_llm

            prev_str = json.dumps(current_extracted, ensure_ascii=False, indent=2)
            result = chain.invoke({
                "ada": ada,
                "text": clean_text,
                "previous_output": prev_str,
                "feedback": feedback,
            })
            
            if isinstance(result, ContractSchema):
                corrected_dict = result.model_dump()
            elif isinstance(result, dict):
                corrected_dict = result
            used_model = target_model
            break
        except Exception as e:
            err_str = str(e)
            # Αν υπάρχει failed_generation με JSON μέσα, το ανακτούμε
            if "failed_generation" in err_str:
                recovered = extract_json_fallback(err_str)
                if recovered:
                    try:
                        # Επαλήθευση μέσω ContractSchema
                        valid_obj = ContractSchema(**recovered)
                        corrected_dict = valid_obj.model_dump()
                        used_model = f"{target_model} (fallback_json)"
                        break
                    except Exception:
                        corrected_dict = recovered
                        break
            print(f"[Corrector Warning] Σφάλμα στο {target_model}: {err_str[:120]}...")
            continue

    elapsed = round(time.time() - start_time, 2)
    metrics["corrector_time_sec"] = metrics.get("corrector_time_sec", 0) + elapsed

    audit_log.append({
        "node": "corrector",
        "retry_step": retries + 1,
        "model_used": used_model,
        "elapsed_sec": elapsed,
    })

    return {
        "extracted_data": corrected_dict,
        "retry_count": retries + 1,
        "is_valid": False,
        "audit_log": audit_log,
        "metrics": metrics,
    }