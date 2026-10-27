
from dataclasses import dataclass
from typing import Any, Literal


CorrectionAction = Literal["finish", "retry"]


@dataclass(frozen=True)
class CorrectionDecision:
    action: CorrectionAction
    next_method: str | None
    reason: str


MAX_RETRIES = 1


def decide_correction(
    final_decisions: dict[str, Any],
    *,
    current_method: str,
    retry_count: int,
    routing: dict[str, Any] | None = None,
) -> CorrectionDecision:
    """Bounded, conservative correction policy."""

    if retry_count >= MAX_RETRIES:
        return CorrectionDecision(
            action="finish",
            next_method=None,
            reason="Retry budget exhausted",
        )

    unresolved = [
        name
        for name, decision in final_decisions.items()
        if decision["final_action"] == "reprocess"
    ]

    if not unresolved:
        return CorrectionDecision(
            action="finish",
            next_method=None,
            reason="No reprocessing required",
        )

    routing = routing or {}
    quality = routing.get("quality", {})

    # Retry OCR only when digital text is suspiciously limited
    # relative to visible page content.
    if (
        current_method == "digital"
        and quality.get("visual_ink_ratio", 0) >= 0.05
        and quality.get("text_chars", 0) < 500
    ):
        return CorrectionDecision(
            action="retry",
            next_method="tesseract",
            reason="Unresolved fields with insufficient digital text",
        )

    return CorrectionDecision(
        action="finish",
        next_method=None,
        reason="No justified alternative processing method",
    )
