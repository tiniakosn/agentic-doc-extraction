import argparse
import json
import sys
from time import perf_counter

from paddleocr import PaddleOCR

from PIL import Image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with Image.open(args.image) as image:
        image_width, image_height = image.size

    start = perf_counter()

    ocr = PaddleOCR(
        text_detection_model_name="PP-OCRv5_mobile_det",
        text_recognition_model_name="el_PP-OCRv5_mobile_rec",
        device="cpu",
        enable_mkldnn=False,
        cpu_threads=2,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )

    results = ocr.predict(args.image)

    lines = []
    regions = []

    for result in results:
        texts = result["rec_texts"]
        boxes = result["rec_boxes"]
        scores = result["rec_scores"]

        for text, box, score in zip(texts, boxes, scores):
            lines.append(text)

            regions.append({
                "text": text,
                "bbox": [float(v) for v in box],
                "confidence": float(score),
            })

    output = {
        "text": "\n".join(lines),
        "regions": regions,
        "engine": "paddleocr",
        "model": "el_PP-OCRv5_mobile_rec",
        "latency_seconds": round(perf_counter() - start, 3),
        "image_width": image_width,
        "image_height": image_height,
    }

    from pathlib import Path

    from pathlib import Path

    Path(args.output).write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()