
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from rapidfuzz.fuzz import ratio


@dataclass(frozen=True)
class RegionMatch:
    region_index: int
    text: str
    score: float
    bbox: tuple[float, float, float, float]


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"\s+", " ", text).strip()


def find_matching_regions(
    value: str,
    regions: list[dict[str, Any]],
    min_score: float = 0.85,
) -> list[RegionMatch]:
    """Find OCR regions containing a candidate field value."""

    normalized_value = normalize(value)
    matches = []

    if not normalized_value:
        return matches

    for index, region in enumerate(regions):
        region_text = normalize(region["text"])

        score = ratio(normalized_value, region_text) / 100

        if score >= min_score:
            matches.append(
                RegionMatch(
                    region_index=index,
                    text=region["text"],
                    score=round(score, 3),
                    bbox=tuple(region["bbox"]),
                )
            )

    return sorted(
        matches,
        key=lambda match: match.score,
        reverse=True,
    )
