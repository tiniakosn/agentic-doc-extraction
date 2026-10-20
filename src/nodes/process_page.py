from time import perf_counter

from src.schemas.document import DocumentRecord
from src.schemas.workflow_state import WorkflowState
from src.ingestion.ocr_backend import TesseractProcessor
from src.ingestion.paddle_backend import PaddleOCRProcessor


def process_page_node(state: WorkflowState) -> dict:
    start = perf_counter()

    method = state.get("processing_method", "tesseract")
    page_number = state.get("page_number", 1)

    if method == "digital":
        document = DocumentRecord.model_validate(state["document"])
        page = document.pages[page_number - 1]

        digital_layer = next(
            (
                layer for layer in page.text_layers
                if layer.method == "digital"
            ),
            None,
        )

        if digital_layer is None:
            raise RuntimeError("Digital text layer not found")

        metrics = dict(state.get("metrics", {}))
        metrics["processing_duration_sec"] = round(
            perf_counter() - start, 3
        )

        return {
            "processed_page": {
                "page_number": page_number,
                "method": "digital",
                "text": digital_layer.text,
                "regions": [],
            },
            "metrics": metrics,
            "status": "processed",
        }

    processors = {
        "tesseract": TesseractProcessor(dpi=300),
        "paddleocr": PaddleOCRProcessor(dpi=150),
    }

    if method not in processors:
        raise ValueError(f"Unsupported processing method: {method}")

    processor = processors[method]

    document = DocumentRecord.model_validate(state["document"])

    layer = processor.process_page(
        state["pdf_path"],
        page_number,
    )

    document.pages[page_number - 1].text_layers.append(layer)

    metrics = dict(state.get("metrics", {}))
    metrics["processing_duration_sec"] = round(
        perf_counter() - start, 3
    )

    return {
        "document": document.model_dump(mode="json"),
        "processed_page": {
            "page_number": page_number,
            "method": layer.method,
            "text": layer.text,
            "regions": [
                region.model_dump(mode="json")
                for region in layer.regions
            ],
        },
        "metrics": metrics,
        "status": "processed",
    }