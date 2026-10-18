import abc
import os
import io
import base64
from typing import List
from PIL import Image
import pytesseract
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage


class BaseOCREngine(abc.ABC):
    """Abstract Strategy Interface για εξαγωγή κειμένου από εικόνες σελίδων."""

    @abc.abstractmethod
    def extract_text(self, image_bytes_list: List[bytes]) -> str:
        pass


class TesseractOCREngine(BaseOCREngine):
    """Τοπικό Open-Source OCR (Μηδενικό API κόστος, offline εκτέλεση)."""

    def extract_text(self, image_bytes_list: List[bytes]) -> str:
        extracted = []
        for idx, img_bytes in enumerate(image_bytes_list):
            try:
                image = Image.open(io.BytesIO(img_bytes))
                text = pytesseract.image_to_string(image, lang="ell+eng", config="--psm 1")
                if text.strip():
                    extracted.append(f"--- ΣΕΛΙΔΑ {idx + 1} (TESSERACT OCR) ---\n{text.strip()}")
            except Exception as e:
                print(f"[Tesseract Error] Σελίδα {idx + 1}: {e}")
        return "\n\n".join(extracted)


class VLMOCREngine(BaseOCREngine):
    """Cloud Vision-Language Model Strategy (Layout-Aware / Multimodal)."""

    def __init__(self, model_name: str = "llama-3.2-11b-vision-preview"):
        self.model_name = model_name

    def extract_text(self, image_bytes_list: List[bytes]) -> str:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Το GROQ_API_KEY απαιτείται για το VLM Engine.")

        llm = ChatGroq(model_name=self.model_name, temperature=0.0)
        content = [
            {
                "type": "text",
                "text": (
                    "Είσαι έμπειρος μεταγραφέας ελληνικών δημόσιων εγγράφων. "
                    "Μετάγραψε ακριβώς το περιεχόμενο του εγγράφου διατηρώντας ΑΔΑ, "
                    "αναδόχους, ΑΦΜ και αριθμητικούς πίνακες."
                ),
            }
        ]

        for img_bytes in image_bytes_list[:4]:
            b64_img = base64.b64encode(img_bytes).decode("utf-8")
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64_img}"},
            })

        try:
            res = llm.invoke([HumanMessage(content=content)])
            return str(res.content)
        except Exception as e:
            print(f"[VLM Fallback] Αποτυχία VLM: {e}. Επιστροφή σε Tesseract.")
            return TesseractOCREngine().extract_text(image_bytes_list)


def get_ocr_engine() -> BaseOCREngine:
    """Factory method επιλογής OCR engine βάσει περιβάλλοντος."""
    provider = os.getenv("OCR_PROVIDER", "local").lower().strip()
    if provider == "vlm":
        return VLMOCREngine()
    return TesseractOCREngine()