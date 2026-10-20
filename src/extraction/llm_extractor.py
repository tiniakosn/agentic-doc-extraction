import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from src.schemas.page_extraction import PageExtraction


MODEL = "qwen/qwen3.8-27b"


def extract_from_text(
    text: str,
    model: str = MODEL,
) -> PageExtraction:
    """Structured extraction from OCR or digital text."""

    if not text.strip():
        raise ValueError("Cannot extract from empty text")

    load_dotenv(dotenv_path=".env")

    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("Missing GROQ_API_KEY")

    llm = ChatGroq(
        model=model,
        temperature=0,
        max_retries=0,
    ).with_structured_output(
        PageExtraction,
        method="json_mode",
    )

    prompt = (
        "Επέστρεψε αποκλειστικά έγκυρο JSON με τα πεδία "
        "document_type, issuing_authority, recipient, "
        "contractor και contractor_tax_id. "
        "Κάθε πεδίο περιέχει value, status, evidence. "
        "Επιτρεπόμενα status: present, not_present, uncertain. "
        "Για present απαιτούνται value και evidence. "
        "Για not_present δώσε value=null και evidence=null. "
        "Για uncertain μην επινοείς πληροφορίες. "
        "Ο παραλήπτης μιας πρόσκλησης δεν είναι απαραίτητα ανάδοχος. "
        "Το OCR μπορεί να έχει λάθη και προβλήματα reading order. "
        "Μη συμπληρώνεις μη τεκμηριωμένα στοιχεία.\n\n"
        f"DOCUMENT TEXT:\n{text}"
    )

    result = llm.invoke([HumanMessage(content=prompt)])

    if isinstance(result, PageExtraction):
        return result

    return PageExtraction.model_validate(result)