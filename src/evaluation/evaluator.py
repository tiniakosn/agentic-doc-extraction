import re


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.upper()
    value = value.replace(".", "")
    value = re.sub(r"\s+", " ", value)

    return value.strip()

def exact_match(prediction: str | None, ground_truth: str | None) -> bool:
    return prediction == ground_truth


def normalized_exact_match(
    prediction: str | None,
    ground_truth: str | None,
) -> bool:
    return normalize_text(prediction) == normalize_text(ground_truth)

def accuracy(results: list[bool]) -> float:
    if not results:
        return 0.0

    return sum(results) / len(results)