import json
from pathlib import Path
from src.evaluation import evaluator

BENCHMARK_PATH = Path("evaluation_results/benchmark_report.json")

ANNOTATIONS_DIR = Path("data/annotations")

DOCUMENT_MAP = {
    "doc_1_digital.pdf": "doc_001.json",
    "doc_2_digital.pdf": "doc_002.json",
    "doc_3_digital.pdf": "doc_003.json",
}


with BENCHMARK_PATH.open(encoding="utf-8") as f:
    predictions = json.load(f)

contractor_results = []

for result in predictions:
    document = result["document"]

    if document not in DOCUMENT_MAP:
        continue

    prediction = result["extracted_data"]["contractor_name"]

    annotation_path = ANNOTATIONS_DIR / DOCUMENT_MAP[document]

    with annotation_path.open(encoding="utf-8") as f:
        ground_truth_data = json.load(f)

    ground_truth = ground_truth_data["contractor"]["name"]["value"]

    print(
        document,
        "prediction =", prediction,
        "| ground_truth =", ground_truth,
    )

    is_match = evaluator.exact_match(prediction, ground_truth)
    contractor_results.append(is_match)

    print(
        document,
        "->",
        "PASS" if is_match else "FAIL",
    )

score = evaluator.accuracy(contractor_results)

print()
print(f"Contractor Raw Exact Match: {score * 100:.2f}%")
print(f"Correct: {sum(contractor_results)}/{len(contractor_results)}")