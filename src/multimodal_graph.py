
from langgraph.graph import StateGraph, START, END

from src.schemas.workflow_state import WorkflowState
from src.nodes.load_document import load_document_node
from src.nodes.assess_and_route import assess_and_route_node
from src.nodes.process_page import process_page_node
from src.nodes.extract_information import extract_information_node
from src.nodes.verify_extraction import verify_extraction_node
from src.nodes.semantic_verification import semantic_verification_node

from src.nodes.correction_controller import (
    correction_controller_node,
    route_after_correction,
)

def route_extraction_strategy(state: WorkflowState) -> str:
    if state.get("extraction_method") == "vlm":
        return "vlm"
    return "text"

def build_multimodal_graph():
    workflow = StateGraph(WorkflowState)

    workflow.add_node("load_document", load_document_node)
    workflow.add_node("assess_and_route", assess_and_route_node)
    workflow.add_node("process_page", process_page_node)
    workflow.add_node("extract_information", extract_information_node)
    workflow.add_node("verify_extraction", verify_extraction_node)
    workflow.add_node("semantic_verification",semantic_verification_node)
    workflow.add_node(
        "correction_controller",
        correction_controller_node,
    )

    workflow.add_edge(START, "load_document")
    workflow.add_edge("load_document", "assess_and_route")
    workflow.add_conditional_edges(
        "assess_and_route",
        route_extraction_strategy,
        {
            "text": "process_page",
            "vlm": "extract_information",
        },
    )
    workflow.add_edge("process_page", "extract_information")
    workflow.add_edge("extract_information", "verify_extraction")
    workflow.add_edge("verify_extraction","semantic_verification")
    workflow.add_edge(
        "semantic_verification",
        "correction_controller",
    )

    workflow.add_conditional_edges(
        "correction_controller",
        route_after_correction,
        {
            "retry": "process_page",
            "finish": END,
        },
    )

    return workflow.compile()
