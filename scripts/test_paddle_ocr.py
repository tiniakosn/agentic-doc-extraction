from pathlib import Path
from time import perf_counter

from paddleocr import PaddleOCR


IMAGE_PATH = "evaluation_results/ocr_experiments/page_1.png"
OUTPUT_PATH = Path(
    "evaluation_results/ocr_experiments/page_1_paddle_150dpi.txt"
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

for result in results:
    print("Available keys:", list(result.keys()))

    texts = result["rec_texts"]
    boxes = result["rec_boxes"]

    for text, box in zip(texts, boxes):
        if "ΠΡΟΣ" in text.upper() or "ΤΣΑΚΟΥΜΗΣ" in text.upper():
            print("Text:", text)
            print("Box:", box.tolist())

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

import json
from pathlib import Path

spatial_results = []

for result in results:
    for text, box, score in zip(
        result["rec_texts"],
        result["rec_boxes"],
        result["rec_scores"],
    ):
        spatial_results.append({
            "text": text,
            "bbox": box.tolist(),
            "confidence": float(score),
        })

Path("evaluation_results/ocr_experiments/page_1_spatial.json").write_text(
    json.dumps(spatial_results, ensure_ascii=False, indent=2),
    encoding="utf-8",
)