from pathlib import Path

import pymupdf

from src.schemas.document import DocumentRecord, DocumentPage, TextLayer


def load_document(pdf_path: str | Path) -> DocumentRecord:
    pdf_path = Path(pdf_path)

    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)

    pages = []

    with pymupdf.open(pdf_path) as pdf:
        for index, page in enumerate(pdf):
            pages.append(
                DocumentPage(
                    page_number=index + 1,
                    text_layers=[
                        TextLayer(
                            method="digital",
                            text=page.get_text("text"),
                        )
                    ],
                )
            )

    return DocumentRecord(
        document_id=pdf_path.stem,
        source="diavgeia",
        pages=pages,
        metadata={"filename": pdf_path.name},
    )