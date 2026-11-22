
from time import perf_counter

from src.evaluation.evidence_retriever import retrieve_evidence
from src.evaluation.claim_verifier import verify_claim
from src.schemas.workflow_state import WorkflowState
from src.evaluation.final_decision import resolve_final_decisions
from src.evaluation.evidence_repair import repair_field_evidence
MAX_SEMANTIC_CHECKS = 2


def semantic_verification_node(state: WorkflowState) -> dict:
    start = perf_counter()

    extraction = state["extraction"]
    decisions = state.get("field_decisions", {})
    processed = state["processed_page"]

    regions = processed.get("regions", [])
    document_id = state["document"]["document_id"]
    page_number = processed["page_number"]
    method = processed["method"]

    results = {}
    checked = 0

    for field_name, decision in decisions.items():
        if checked >= MAX_SEMANTIC_CHECKS:
            break

        if decision["action"] not in ("reprocess", "review"):
            continue

        # A deterministic failure cannot be resolved by an LLM.
        if decision.get("decision_source") == "deterministic_validation":
            continue

        field = extraction[field_name]

        if field.get("status") != "present" or not field.get("value"):
            continue

        candidates = retrieve_evidence(
            field["value"],
            regions,
            document_id=document_id,
            page_number=page_number,
            method=method,
        )

        if not candidates:
            results[field_name] = {
                "verdict": "insufficient_evidence",
                "reason": "No evidence candidates found",
            }
            continue

        result = verify_claim(
            field_name=field_name,
            claimed_value=field["value"],
            candidates=candidates,
        )

        results[field_name] = result.model_dump(mode="json")
        checked += 1

    final_decisions = resolve_final_decisions(
        field_decisions=decisions,
        semantic_verification=results,
    )

    evidence_repairs = repair_field_evidence(
        extraction=extraction,
        verification=state["verification"],
        final_decisions=final_decisions,
    )

    metrics = dict(state.get("metrics", {}))
    metrics["semantic_verification_duration_sec"] = round(
        perf_counter() - start, 3
    )

    return {
        "semantic_verification": results,
        "metrics": metrics,
        "status": "semantically_verified",
        "final_decisions": final_decisions,
        "evidence_repairs": evidence_repairs,
    }
