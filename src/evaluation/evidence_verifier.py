
import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from rapidfuzz.fuzz import partial_ratio


VerificationStatus = Literal[
    "supported",
    "unsupported",
    "needs_review",
]


@dataclass(frozen=True)
class EvidenceResult:
    status: VerificationStatus
    score: float
    matched_text: str | None = None


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.casefold()

    # Normalize whitespace only; preserve punctuation and digits.
    return re.sub(r"\s+", " ", text).strip()


def verify_evidence(
    evidence: str | None,
    source_text: str,
    threshold: float = 0.90,
) -> EvidenceResult:
    if not evidence:
        return EvidenceResult(
            status="needs_review",
            score=0.0,
        )

    normalized_evidence = normalize(evidence)
    normalized_source = normalize(source_text)

    if normalized_evidence in normalized_source:
        return EvidenceResult(
            status="supported",
            score=1.0,
            matched_text=evidence,
        )

    # Fuzzy similarity is only a review signal, not proof.
    similarity = partial_ratio(
        normalized_evidence,
        normalized_source,
    ) / 100

    if similarity >= threshold:
        return EvidenceResult(
            status="needs_review",
            score=similarity,
        )

    return EvidenceResult(
        status="unsupported",
        score=similarity,
    )
