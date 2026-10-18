import base64
import os
from pathlib import Path
from time import perf_counter

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

load_dotenv(dotenv_path=".env")

IMAGE_PATH = Path(
    "evaluation_results/ocr_experiments/page_4_150dpi.png"
)

OUTPUT_PATH = Path(
    "evaluation_results/ocr_experiments/page_4_qwen.txt"
)

MODEL = "qwen/qwen3.8-27b"


def main():
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("Missing GROQ_API_KEY")

    image_bytes = IMAGE_PATH.read_bytes()
    image_b64 = base64.b64encode(image_bytes).decode("ascii")

    llm = ChatGroq(
        model=MODEL,
        temperature=0,
        max_retries=0,
    )

    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": (
                    "Μετάγραψε πιστά το ορατό κείμενο "
                    "της εικόνας στα ελληνικά. "
                    "Μην το συνοψίσεις και μην συμπληρώνεις "
                    "πληροφορίες που δεν διακρίνονται. "
                    "Διατήρησε ακριβώς αριθμούς, ΑΦΜ, "
                    "νομικές αναφορές και ποσά. "
                    "Επέστρεψε μόνο τη μεταγραφή."
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
    response = llm.invoke([message])
    print("Response metadata:", response.response_metadata)
    elapsed = perf_counter() - start

    text = response.content

    if not isinstance(text, str):
        raise TypeError("Unexpected VLM response format")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(text, encoding="utf-8")

    print("Model:", MODEL)
    print("Characters:", len(text.strip()))
    print("Latency:", round(elapsed, 2), "seconds")
    print("Token usage:", response.usage_metadata)
    print()
    print(text[:1200])


if __name__ == "__main__":
    main()