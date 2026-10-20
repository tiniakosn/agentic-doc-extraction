
from langgraph.graph import StateGraph, START, END

from src.schemas.workflow_state import WorkflowState
from src.nodes.load_document import load_document_node
from src.nodes.assess_and_route import assess_and_route_node
from src.nodes.process_page import process_page_node
from src.nodes.extract_information import extract_information_node
from src.nodes.verify_extraction import verify_extraction_node


def build_multimodal_graph():
    workflow = StateGraph(WorkflowState)

    workflow.add_node("load_document", load_document_node)
    workflow.add_node("assess_and_route", assess_and_route_node)
    workflow.add_node("process_page", process_page_node)
    workflow.add_node("extract_information", extract_information_node)
    workflow.add_node("verify_extraction", verify_extraction_node)

    workflow.add_edge(START, "load_document")
    workflow.add_edge("load_document", "assess_and_route")
    workflow.add_edge("assess_and_route", "process_page")
    workflow.add_edge("process_page", "extract_information")
    workflow.add_edge("extract_information", "verify_extraction")
    workflow.add_edge("verify_extraction", END)

    return workflow.compile()
