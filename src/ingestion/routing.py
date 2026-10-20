
from dataclasses import dataclass
from typing import Literal

from src.ingestion.page_quality import PageQuality


ProcessingRoute = Literal[
    "digital",
    "tesseract",
    "review",
]


@dataclass(frozen=True)
class RoutingDecision:
    route: ProcessingRoute
    reason: str


def choose_processing_route(
    quality: PageQuality,
) -> RoutingDecision:
    """Initial rule-based routing baseline."""

    if (
        quality.text_chars >= 500
        and quality.suspicious_text_ratio < 0.02
    ):
        return RoutingDecision(
            route="digital",
            reason="Sufficient digital text",
        )

    if (
        quality.image_coverage >= 0.5
        and quality.text_chars < 500
    ):
        return RoutingDecision(
            route="tesseract",
            reason="Image-dominant page with limited digital text",
        )

    if quality.text_chars < 200:
        return RoutingDecision(
            route="tesseract",
            reason="Very limited digital text",
        )

    return RoutingDecision(
        route="review",
        reason="Ambiguous digital text quality",
    )


def choose_processing_route_v2(
    quality: PageQuality,
) -> RoutingDecision:
    """
    Experimental quality-aware routing policy.

    Thresholds are provisional and must be evaluated.
    """

    # Low visual density: do not automatically run OCR.
    if (
        quality.visual_ink_ratio < 0.03
        and quality.text_chars < 500
    ):
        return RoutingDecision(
            route="review",
            reason="Low visual density; content relevance uncertain",
        )

    # Image-dominant pages with limited digital text.
    if (
        quality.image_coverage >= 0.5
        and quality.text_chars < 500
    ):
        return RoutingDecision(
            route="tesseract",
            reason="Image-dominant page with limited digital text",
        )

    # Visually dense pages with insufficient digital text.
    if (
        quality.visual_ink_ratio >= 0.05
        and quality.text_chars < 500
    ):
        return RoutingDecision(
            route="tesseract",
            reason="Visible content exceeds available digital text",
        )

    # Digital text appears sufficient for Greek documents.
    if (
        quality.text_chars >= 500
        and quality.greek_letter_ratio >= 0.5
        and quality.suspicious_text_ratio < 0.02
    ):
        return RoutingDecision(
            route="digital",
            reason="Sufficient Greek digital text",
        )

    return RoutingDecision(
        route="review",
        reason="Ambiguous text quality",
    )
