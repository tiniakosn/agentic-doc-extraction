import json
from pathlib import Path
from pydantic import ValidationError
from src.schemas.annotations import DocumentAnnotation


ANNOTATIONS_DIR = Path("data/annotations")

annotation_files = sorted(ANNOTATIONS_DIR.glob("*.json"))

for file_path in annotation_files:
    try:
        with file_path.open(encoding="utf-8") as f:
            data = json.load(f)

        DocumentAnnotation.model_validate(data)

        print(f"✓ {file_path.name}")

    except (ValidationError, json.JSONDecodeError) as error:
        print(f"✗ {file_path.name}")
        print(error)
