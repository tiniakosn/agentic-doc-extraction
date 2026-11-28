
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


def _fold_tokens(text: str) -> list[str]:
    """Casefold, strip accents, split into word tokens."""
    text = unicodedata.normalize("NFD", text.casefold())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.findall(r"\w+", text)


def morphological_match(
    value: str | None,
    source_text: str,
    *,
    min_stem: int = 4,
    suffix: int = 3,
) -> bool:
    """True if the value's tokens appear consecutively in the source,
    allowing inflectional suffix changes (e.g. Greek grammatical case).

    Tokens containing digits must match exactly (tax IDs, numbers).
    """
    if not value or not source_text:
        return False

    value_tokens = _fold_tokens(value)
    source_tokens = _fold_tokens(source_text)

    if not value_tokens:
        return False

    stems = [
        token
        if any(ch.isdigit() for ch in token)
        else token[:max(min_stem, len(token) - suffix)]
        for token in value_tokens
    ]

    n = len(stems)

    for i in range(len(source_tokens) - n + 1):
        if all(
            source_tokens[i + j].startswith(stems[j])
            if not any(ch.isdigit() for ch in stems[j])
            else source_tokens[i + j] == stems[j]
            for j in range(n)
        ):
            return True

    return False