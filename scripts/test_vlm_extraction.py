
import base64
import json
import os
from pathlib import Path
from time import perf_counter

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from src.schemas.page_extraction import PageExtraction


load_dotenv(dotenv_path=".env")

MODEL = "qwen/qwen3.8-27b"

IMAGE_PATH = Path(
    "evaluation_results/ocr_experiments/page_1.png"
)

OUTPUT_PATH = Path(
    "evaluation_results/vlm_extraction_page1.json"
)


def main():
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("Missing GROQ_API_KEY")

    image_b64 = base64.b64encode(
        IMAGE_PATH.read_bytes()
    ).decode("ascii")

    llm = ChatGroq(
        model=MODEL,
        temperature=0,
        max_retries=0,
    ).with_structured_output(
        PageExtraction,
        method="json_mode",
    )

    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": (
                    "ΥΠΟΧΡΕΩΤΙΚΟ OUTPUT SCHEMA:\n"
                    "Κάθε πεδίο πρέπει να είναι JSON object με "
                    "value, status και evidence.\n"
                    "Το status επιτρέπεται να έχει ΑΠΟΚΛΕΙΣΤΙΚΑ "
                    "μία από τις τιμές: present, not_present, uncertain.\n"
                    "ΜΗ χρησιμοποιείς confirmed, found, missing ή άλλες τιμές.\n"
                    "Για status=present δώσε value και evidence.\n"
                    "Για status=not_present δώσε value=null και evidence=null.\n"
                    "Για status=uncertain μην επινοείς τιμές.\n"
                    'Παράδειγμα: {"recipient": {"value": "ΕΤΑΙΡΕΙΑ Α", '
                    '"status": "present", "evidence": "ΠΡΟΣ: ΕΤΑΙΡΕΙΑ Α"}}. '
                    "Επέστρεψε αποκλειστικά ένα έγκυρο JSON object "
                    "που ακολουθεί το PageExtraction schema. "
                    "Κάθε πεδίο πρέπει να είναι object με value, status και evidence. "
                    "Ανάλυσε ΜΟΝΟ την εικόνα της συγκεκριμένης "
                    "σελίδας ελληνικού δημόσιου εγγράφου. "
                    "Εξήγαγε document_type, issuing_authority, "
                    "recipient, contractor και contractor_tax_id. "
                    "Για κάθε πεδίο επέστρεψε value, status και "
                    "ακριβές evidence από τη σελίδα. "
                    "ΠΡΟΣΟΧΗ: Ο παραλήπτης μιας πρόσκλησης "
                    "δεν είναι απαραίτητα ανάδοχος. "
                    "Μη συμπεραίνεις ανάθεση αν δεν υπάρχει "
                    "ρητή τεκμηρίωση. "
                    "Αν ένα πεδίο δεν εμφανίζεται, δήλωσε "
                    "not_present. Αν δεν διαβάζεται με "
                    "βεβαιότητα, δήλωσε uncertain. "
                    "Μη συμπληρώνεις πληροφορίες από υποθέσεις."
                ),
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_b64}"
                },
            },
        ]
    )

    start = perf_counter()
    result = llm.invoke([message])
    elapsed = perf_counter() - start

    if not isinstance(result, PageExtraction):
        result = PageExtraction.model_validate(result)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_PATH.write_text(
        result.model_dump_json(indent=2),
        encoding="utf-8",
    )

    print("Model:", MODEL)
    print("Latency:", round(elapsed, 2), "seconds")
    print(json.dumps(
        result.model_dump(),
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
