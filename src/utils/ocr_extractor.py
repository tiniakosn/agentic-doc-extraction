import io
from typing import List
from PIL import Image
import pytesseract


def extract_text_with_local_ocr(image_bytes_list: List[bytes]) -> str:
    """
    Εξάγει κείμενο από λίστα εικόνων (PNG bytes) χρησιμοποιώντας τοπικό Tesseract OCR.
    Υποστηρίζει παράλληλα ελληνικά και αγγλικά (ell+eng) για κωδικούς/ΑΔΑ.
    """
    extracted_pages = []

    for idx, img_bytes in enumerate(image_bytes_list):
        try:
            image = Image.open(io.BytesIO(img_bytes))
            # psm 1: Αυτόματος εντοπισμός layout και προσανατολισμού σελίδας
            text = pytesseract.image_to_string(image, lang="ell+eng", config="--psm 1")
            clean_text = text.strip()
            if clean_text:
                extracted_pages.append(f"--- ΣΕΛΙΔΑ {idx + 1} (OCR) ---\n{clean_text}")
        except Exception as e:
            print(f"[OCR Error] Σφάλμα στη σελίδα {idx + 1}: {e}")

    return "\n\n".join(extracted_pages)