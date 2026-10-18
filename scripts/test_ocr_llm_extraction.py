
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

OCR_PATH = Path(
    "evaluation_results/ocr_experiments/page_1_paddle.txt"
)

OUTPUT_PATH = Path(
    "evaluation_results/ocr_llm_extraction_page1.json"
)


def main():
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("Missing GROQ_API_KEY")

    ocr_text = OCR_PATH.read_text(encoding="utf-8")

    llm = ChatGroq(
        model=MODEL,
        temperature=0,
        max_retries=0,
    ).with_structured_output(
        PageExtraction,
        method="json_mode",
    )

    prompt = (
        "Επέστρεψε αποκλειστικά έγκυρο JSON σύμφωνα με "
        "το PageExtraction schema. "
        "Για ΚΑΘΕ πεδίο (document_type, issuing_authority, "
        "recipient, contractor, contractor_tax_id), "
        "επέστρεψε object με value, status, evidence. "
        "Το status πρέπει να είναι αποκλειστικά "
        "present, not_present ή uncertain. "
        "Για present δώσε value και ακριβές evidence. "
        "Για not_present δώσε value=null και evidence=null. "
        "Αν το κείμενο δεν επαρκεί, χρησιμοποίησε uncertain. "
        "ΠΡΟΣΟΧΗ: Ο παραλήπτης μιας πρόσκλησης δεν είναι "
        "απαραίτητα ανάδοχος. Μην επινοείς ανάθεση. "
        "Το OCR ενδέχεται να έχει λάθη και ανακατεμένη "
        "σειρά ανάγνωσης.\n\n"
        "OCR TEXT:\n"
        f"{ocr_text}"
    )

    start = perf_counter()

    result = llm.invoke([
        HumanMessage(content=prompt)
    ])

    elapsed = perf_counter() - start

    if not isinstance(result, PageExtraction):
        result = PageExtraction.model_validate(result)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        result.model_dump_json(indent=2),
        encoding="utf-8",
    )

    print("Model:", MODEL)
    print("LLM latency:", round(elapsed, 2), "seconds")
    print(json.dumps(
        result.model_dump(),
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
