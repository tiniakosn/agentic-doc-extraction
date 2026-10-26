
import re
import unicodedata
from typing import Any

from rapidfuzz.fuzz import ratio

from src.schemas.evidence import SourceReference
from src.schemas.verification import EvidenceCandidate


def normalize_tokens(text: str) -> list[str]:
    text = unicodedata.normalize("NFD", text.casefold())
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )
    return re.findall(r"\w+", text)


def token_similarity(a: str, b: str) -> float:
    return ratio(a, b) / 100


def token_coverage(query: str, candidate: str) -> float:
    query_tokens = normalize_tokens(query)
    candidate_tokens = normalize_tokens(candidate)

    if not query_tokens:
        return 0.0

    matched = 0

    for query_token in query_tokens:
        best = max(
            (
                token_similarity(query_token, token)
                for token in candidate_tokens
            ),
            default=0.0,
        )

        if best >= 0.8:
            matched += 1

    return matched / len(query_tokens)


def retrieve_evidence(
    value: str,
    regions: list[dict[str, Any]],
    *,
    document_id: str,
    page_number: int,
    method: str,
    top_k: int = 5,
    min_score: float = 0.5,
) -> list[EvidenceCandidate]:

    candidates = []

    for index, region in enumerate(regions):
        score = token_coverage(value, region["text"])

        if score < min_score:
            continue

        source = SourceReference(
            document_id=document_id,
            page_number=page_number,
            method=method,
            region_index=index,
            text=region["text"],
            bbox=region["bbox"],
            normalized_bbox=region.get("normalized_bbox"),
        )

        candidates.append(
            EvidenceCandidate(
                source=source,
                retrieval_score=round(score, 3),
                retrieval_method="fuzzy_token_coverage",
            )
        )

    return sorted(
        candidates,
        key=lambda item: item.retrieval_score,
        reverse=True,
    )[:top_k]
