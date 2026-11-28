from unittest.mock import patch
import pymupdf
from src.multimodal_graph import build_multimodal_graph
from unittest.mock import patch
from src.schemas.verification import ClaimVerification
from src.ingestion.routing import RoutingDecision
from src.schemas.document import (
    DocumentRecord,
    DocumentPage,
    TextLayer,
    TextRegion,
)
from src.schemas.page_extraction import PageExtraction

def test_multimodal_graph_compiles():

    graph = build_multimodal_graph()

    assert graph is not None
    assert "correction_controller" in graph.get_graph().nodes

def make_extraction(afm: str) -> PageExtraction:
    """Create a controlled extraction for integration testing."""

    return PageExtraction.model_validate({
        "document_type": {
            "status": "present",
            "value": "award_decision",
            "evidence": "ΑΠΟΦΑΣΗ",
        },
        "issuing_authority": {
            "status": "present",
            "value": "Δήμος Ανατολικής Σάμου",
            "evidence": "ΔΗΜΟΣ ΑΝΑΤΟΛΙΚΗΣ ΣΑΜΟΥ",
        },
        "recipient": {
            "status": "not_present",
            "value": None,
            "evidence": None,
        },
        "contractor": {
            "status": "present",
            "value": "ΔΗΜΗΤΡΙΟΣ ΚΑΝΑΡΗΣ ΚΑΙ ΣΙΑ ΟΕ",
            "evidence": "ΔΗΜΗΤΡΙΟΣ ΚΑΝΑΡΗΣ ΚΑΙ ΣΙΑ ΟΕ",
        },
        "contractor_tax_id": {
            "status": "present",
            "value": afm,
            "evidence": f"ΑΦΜ: {afm}",
        },
    })

def test_extraction_fixtures():
    wrong = make_extraction("6983905183")
    correct = make_extraction("801033798")

    assert wrong.contractor_tax_id.value == "6983905183"
    assert correct.contractor_tax_id.value == "801033798"
    assert wrong.contractor_tax_id.status == "present"
    assert correct.contractor_tax_id.status == "present"


from src.schemas.document import TextLayer


def test_vlm_to_ocr_correction_loop(tmp_path):
    pdf_path = tmp_path / "mock.pdf"

    with pymupdf.open() as pdf:
        pdf.new_page()
        pdf.save(pdf_path)


    graph = build_multimodal_graph()

    document = DocumentRecord(
        document_id="test_samos",
        source=str(pdf_path),
        pages=[DocumentPage(page_number=1)],
    )

    ocr_text = (
        "ΑΠΟΦΑΣΗ\n"
        "ΔΗΜΟΣ ΑΝΑΤΟΛΙΚΗΣ ΣΑΜΟΥ\n"
        "ΔΗΜΗΤΡΙΟΣ ΚΑΝΑΡΗΣ ΚΑΙ ΣΙΑ ΟΕ\n"
        "ΑΦΜ: 801033798"
    )

    ocr_layer = TextLayer(
        method="tesseract",
        text=ocr_text,
    )

    observed_texts = []
    observed_feedback = []

    def fake_text_extraction(text, feedback=None):
        observed_texts.append(text)
        observed_feedback.append(feedback)
        return make_extraction("801033798")
    with (

        patch(
            "src.nodes.semantic_verification.verify_claim",
            return_value=ClaimVerification(
                field_name="contractor",
                claimed_value="ΔΗΜΗΤΡΙΟΣ ΚΑΝΑΡΗΣ ΚΑΙ ΣΙΑ ΟΕ",
                verdict="insufficient_evidence",
                explanation="Mocked semantic verification",
                verification_method="mock_semantic",
            ),
        ),

        patch(
            "src.nodes.load_document.load_document",
            return_value=document,
        ),
        patch(
            "src.nodes.assess_and_route.choose_processing_route_v2",
            return_value=RoutingDecision(
                route="review",
                reason="Controlled integration test",
            ),
        ),
        patch(
            "src.nodes.extract_information.extract_from_image",
            return_value=make_extraction("6983905183"),
        ),
        patch(
            "src.nodes.extract_information.extract_from_text",
            side_effect=fake_text_extraction,
        ),
        patch(
            "src.nodes.process_page.TesseractProcessor.process_page",
            return_value=ocr_layer,
        ),
    ):
        result = graph.invoke({
            "pdf_path": str(pdf_path),
            "page_number": 1,
            "extraction_method": "vlm",
            "retry_count": 0,
        })

    assert result["retry_count"] == 1
    assert result["processing_method"] == "tesseract"
    assert result["extraction_method"] == "text"

    assert len(result["correction_history"]) == 1

    previous = result["correction_history"][0][
        "previous_extraction"
    ]

    assert previous["contractor_tax_id"]["value"] == "6983905183"

    assert len(observed_texts) == 1
    assert observed_texts[0] == ocr_text

    assert result["extraction"]["contractor_tax_id"]["value"] == "801033798"
    assert result["processed_page"]["method"] == "tesseract"

    assert result["verification"]["contractor_tax_id"][
        "deterministic_validation"
    ]["status"] == "valid"

    assert result["final_decisions"]["contractor_tax_id"][
        "final_action"
    ] != "reprocess"

    assert result["correction_action"] == "finish"
    assert result["status"] in ("completed", "review_required")

    # Reflection: the retry received feedback about the rejected AFM.
    assert observed_feedback[0] is not None
    assert "6983905183" in observed_feedback[0]
    assert result["correction_history"][0]["action"] == "retry"