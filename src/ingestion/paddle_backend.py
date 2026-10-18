
import json
import subprocess
import tempfile
from pathlib import Path
from time import perf_counter

import pymupdf

from src.schemas.document import TextLayer, TextRegion


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class PaddleOCRProcessor:
    def __init__(self, dpi: int = 150, timeout: int = 180):
        self.dpi = dpi
        self.timeout = timeout
        self.python_executable = PROJECT_ROOT / ".venv-ocr/bin/python"
        self.worker_script = PROJECT_ROOT / "scripts/paddle_worker.py"

    def process_page(
        self,
        pdf_path: str | Path,
        page_number: int,
    ) -> TextLayer:
        start = perf_counter()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            image_path = temp_dir / "page.png"
            output_path = temp_dir / "result.json"

            with pymupdf.open(pdf_path) as pdf:
                if not 1 <= page_number <= len(pdf):
                    raise ValueError("Invalid page number")

                pdf[page_number - 1].get_pixmap(
                    dpi=self.dpi,
                    alpha=False,
                ).save(image_path)

            result = subprocess.run(
                [
                    str(self.python_executable),
                    str(self.worker_script),
                    "--image",
                    str(image_path),
                    "--output",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=PROJECT_ROOT,
                check=False,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"PaddleOCR worker failed: {result.stderr[-1000:]}"
                )

            if not output_path.exists():
                raise RuntimeError("PaddleOCR did not produce output JSON")

            data = json.loads(output_path.read_text(encoding="utf-8"))

            width = data["image_width"]
            height = data["image_height"]

            regions = []

            for region in data["regions"]:
                x1, y1, x2, y2 = region["bbox"]

                regions.append(
                    TextRegion(
                        text=region["text"],
                        bbox=(x1, y1, x2, y2),
                        normalized_bbox=(
                            x1 / width,
                            y1 / height,
                            x2 / width,
                            y2 / height,
                        ),
                        confidence=region["confidence"],
                    )
                )

        return TextLayer(
            method="paddleocr",
            text=data["text"],
            model_name=data["model"],
            latency_seconds=round(perf_counter() - start, 3),
            regions=regions,
            image_width=width,
            image_height=height,
        )

    