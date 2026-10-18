from pathlib import Path
from time import perf_counter

from paddleocr import PaddleOCR


IMAGE_PATH = "evaluation_results/ocr_experiments/page_4_150dpi.png"
OUTPUT_PATH = Path(
    "evaluation_results/ocr_experiments/page_4_paddle_150dpi.txt"
)

ocr = PaddleOCR(
    lang="el",
    ocr_version="PP-OCRv5",
    text_detection_model_name="PP-OCRv5_mobile_det",
    text_recognition_model_name="el_PP-OCRv5_mobile_rec",
    device="cpu",
    enable_mkldnn=False,
    cpu_threads=2,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
)

start = perf_counter()

results = ocr.predict(IMAGE_PATH)

elapsed = perf_counter() - start

lines = []

for result in results:
    lines.extend(result["rec_texts"])

text = "\n".join(lines)

OUTPUT_PATH.write_text(text, encoding="utf-8")

print("OCR characters:", len(text.strip()))
print("Processing time:", round(elapsed, 2), "seconds")
print("Saved:", OUTPUT_PATH)
print()
print(text[:1500])