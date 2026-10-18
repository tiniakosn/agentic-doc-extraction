import base64
import os
from typing import List
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

load_dotenv()

VISION_MODEL = "llama-3.2-11b-vision-preview"


def get_vision_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Το GROQ_API_KEY δεν βρέθηκε.")
    return ChatGroq(model_name=VISION_MODEL, temperature=0.0)


def extract_text_from_images(image_bytes_list: List[bytes]) -> str:
    """
    Μετατρέπει τις εικόνες σελίδων σε ενιαίο κείμενο μέσω Vision LLM.
    """
    if not image_bytes_list:
        return ""

    llm = get_vision_llm()
    content = [
        {
            "type": "text",
            "text": (
                "Είσαι εξειδικευμένος μεταγραφέας ελληνικών δημοσίων εγγράφων. "
                "Μετάγραψε πιστά όλο το κείμενο που βλέπεις στην εικόνα του εγγράφου, "
                "δίνοντας ιδιαίτερη έμφαση στον ΑΔΑ, στον τίτλο, στα στοιχεία του αναδόχου (επωνυμία, ΑΦΜ) "
                "και στους πίνακες ποσών/δαπανών."
            ),
        }
    ]

    # Προσθήκη των πρώτων σελίδων σε Base64 (συνήθως 1-2 σελίδες αρκούν)
    for img_bytes in image_bytes_list[:2]:
        b64_img = base64.b64encode(img_bytes).decode("utf-8")
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64_img}"},
        })

    message = HumanMessage(content=content)
    
    try:
        response = llm.invoke([message])
        return str(response.content)
    except Exception as e:
        print(f"[Vision Error] Αποτυχία Vision LLM: {e}")
        return ""