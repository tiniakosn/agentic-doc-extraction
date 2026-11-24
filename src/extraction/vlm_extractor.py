
import base64
import os

import pymupdf

from src.extraction.llm_client import get_llm
from langchain_core.messages import HumanMessage

from src.schemas.page_extraction import PageExtraction
from src.extraction.llm_extractor import MODEL


def extract_from_image(
    pdf_path: str,
    page_number: int,
    model: str = MODEL,
    dpi: int = 150,
) -> PageExtraction:
    """Extract structured fields directly from a PDF page image."""

    load_dotenv(dotenv_path=".env")

    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("Missing GROQ_API_KEY")

    with pymupdf.open(pdf_path) as doc:
        if not 1 <= page_number <= len(doc):
            raise ValueError(f"Invalid page number: {page_number}")

        pix = doc[page_number - 1].get_pixmap(
            dpi=dpi,
            alpha=False,
        )

        image_bytes = pix.tobytes("png")

    image_b64 = base64.b64encode(
        image_bytes
    ).decode("ascii")

    llm = get_llm(
        model_name=model,
        temperature=0,
        max_retries=0,
    ).with_structured_output(
        PageExtraction,
        method="json_mode",
    )

    prompt = (
        "Ανάλυσε τη συγκεκριμένη σελίδα ελληνικού "
        "δημόσιου εγγράφου και επέστρεψε αποκλειστικά "
        "έγκυρο JSON σύμφωνα με το PageExtraction schema. "
        "Εξήγαγε document_type, issuing_authority, "
        "recipient, contractor και contractor_tax_id. "
        "Κάθε πεδίο πρέπει να έχει value, status, evidence. "
        "Επιτρεπόμενα status: present, not_present, uncertain. "
        "Για present δώσε value και evidence. "
        "Για not_present δώσε value=null και evidence=null. "
        "Για uncertain μην επινοείς τιμές. "
        "Ο παραλήπτης μιας πρόσκλησης δεν είναι απαραίτητα "
        "ανάδοχος. Μην υποθέτεις ανάθεση χωρίς ρητή "
        "τεκμηρίωση. "
        "Το evidence πρέπει να προέρχεται από το ορατό "
        "κείμενο της εικόνας. "
        "Μην συμπληρώνεις πληροφορίες από υποθέσεις."
    )

    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": prompt,
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_b64}",
                },
            },
        ]
    )

    result = llm.invoke([message])

    if isinstance(result, PageExtraction):
        return result

    return PageExtraction.model_validate(result)
