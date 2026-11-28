from time import perf_counter

from src.evaluation.absence_check import check_absence
from src.evaluation.evidence_verifier import verify_evidence, morphological_match
from src.evaluation.region_grounding import find_matching_regions
from src.evaluation.spatial_verifier import compare_boxes
from src.evaluation.source_anchor import anchor_value
from src.schemas.workflow_state import WorkflowState
from src.evaluation.verification_decision import decide_field_action
from src.evaluation.field_validation import validate_greek_afm


ROLE_LABELS = {
    "recipient": "ΠΡΟΣ:",
}

# Fields whose value is a category, not a quotation from the source.
CLASSIFICATION_FIELDS = {"document_type"}


def verify_extraction_node(state: WorkflowState) -> dict:
    start = perf_counter()

    extraction = state["extraction"]
    processed_page = state["processed_page"]

    source_text = processed_page["text"]
    regions = processed_page.get("regions", [])

    document = state.get("document", {})
    document_id = document.get("document_id", "")

    page_number = processed_page.get(
        "page_number",
        state.get("page_number", 1),
    )
    method = processed_page.get("method", "unknown")

    pages = document.get("pages", [])
    page_layers = (
        pages[page_number - 1].get("text_layers", [])
        if 1 <= page_number <= len(pages)
        else []
    )

    selected_layer = next(
        (
            layer
            for layer in reversed(page_layers)
            if layer.get("method") == method
        ),
        {},
    )

    image_width = selected_layer.get("image_width")
    image_height = selected_layer.get("image_height")

    verification = {}

    for field_name, field in extraction.items():

        deterministic_validation = None

        if (
            field_name == "contractor_tax_id"
            and field["status"] == "present"
        ):
            is_valid = validate_greek_afm(field["value"])

            deterministic_validation = {
                "status": "valid" if is_valid else "invalid",
                "reason": (
                    "Valid Greek AFM format and checksum"
                    if is_valid
                    else "Invalid Greek AFM format or checksum"
                ),
            }

        # Fields without an asserted value
        if field["status"] != "present":
            absence = (
                check_absence(field_name, source_text)
                if field["status"] == "not_present"
                else None
            )
            checkable = bool(absence) and absence["status"] != "not_checkable"

            verification[field_name] = {
                "value_grounding": None,
                "evidence_matching": None,
                "spatial_grounding": None,
                "source_references": [],
                "absence_check": absence,
                "verification_status": (
                    "absence_checked" if checkable else "not_checked"
                ),
                "review_required": not (
                    absence and absence["status"] == "supported"
                ),
                "reason": absence["reason"] if absence else "Field is uncertain",
            }
            continue

        # 1. Textual value grounding (not applicable to classifications)
        if field_name in CLASSIFICATION_FIELDS:
            value_grounding = {"status": "not_applicable", "score": None}
        else:
            value_result = verify_evidence(field["value"], source_text)
            value_grounding = {
                "status": value_result.status,
                "score": round(value_result.score, 3),
            }
                        # Greek inflection: the value may appear in another grammatical case.
            if (
                value_result.status != "supported"
                and morphological_match(field["value"], source_text)
            ):
                value_grounding = {
                    "status": "supported",
                    "score": round(value_result.score, 3),
                    "method": "morphological",
                }

        # 2. LLM-generated evidence matching
        evidence_result = verify_evidence(
            field["evidence"],
            source_text,
        )

        # 3. Source-anchored region references
        references = (
            anchor_value(
                field["value"],
                regions,
                document_id=document_id,
                page_number=page_number,
                method=method,
                image_width=image_width,
                image_height=image_height,
            )
            if regions and document_id
            and field_name not in CLASSIFICATION_FIELDS
            else []
        )

        # 4. Spatial role grounding
        spatial_result = None

        if field_name in ROLE_LABELS and regions:
            value_matches = find_matching_regions(
                field["value"],
                regions,
            )
            label_matches = find_matching_regions(
                ROLE_LABELS[field_name],
                regions,
            )

            if value_matches and label_matches:
                value_region = value_matches[0]
                label_region = label_matches[0]

                relation = compare_boxes(
                    list(label_region.bbox),
                    list(value_region.bbox),
                )

                spatial_result = {
                    "label_region": label_region.region_index,
                    "value_region": value_region.region_index,
                    "horizontal_gap": relation.horizontal_gap,
                    "vertical_gap": relation.vertical_gap,
                    "nearby": relation.is_nearby,
                    "right_of_label": relation.is_right_of,
                }

        verification[field_name] = {
            "value_grounding": value_grounding,
            "evidence_matching": {
                "status": evidence_result.status,
                "score": round(evidence_result.score, 3),
            },
            "spatial_grounding": spatial_result,
            "source_references": [
                reference.model_dump(mode="json")
                for reference in references
            ],
            "deterministic_validation": deterministic_validation,
            "verification_status": "checked",
            "review_required": (
                value_grounding["status"] not in ("supported", "not_applicable")
                or evidence_result.status != "supported"
            ),
        }

    field_decisions = {}

    for field_name, checks in verification.items():
        decision = decide_field_action(checks)

        field_decisions[field_name] = {
            "action": decision.action,
            "reason": decision.reason,
            "decision_source": decision.decision_source,
        }

    metrics = dict(state.get("metrics", {}))
    metrics["verification_duration_sec"] = round(
        perf_counter() - start, 3
    )

    return {
        "verification": verification,
        "metrics": metrics,
        "status": "verified",
        "field_decisions": field_decisions,
    }