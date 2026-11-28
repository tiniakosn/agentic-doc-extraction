"""Shared value normalization for the pipeline and evaluation scripts.

Conservative: removes accents, case and extra whitespace.
It does NOT perform identity resolution (e.g. abbreviations).
"""
import re
import unicodedata


def normalized(value):
    """Accents/case/whitespace normalization."""
    if value is None:
        return None
    s = unicodedata.normalize("NFKC", str(value))
    s = "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )
    s = s.casefold()
    return " ".join(s.split())


def normalize_document_type(value):
    """Map well-supported document-type synonyms to canonical types."""
    s = normalized(value)
    if not s:
        return s

    canonical_types = {
        "award_decision",
        "invitation",
        "commitment_decision",
        "administrative_order",
        "administrative_decision",
        "contract_summary",
    }

    if s in canonical_types:
        return s
    if "αναληψη" in s and "υποχρεωσ" in s:
        return "commitment_decision"
    if "περιληψη συμβαση" in s or "contract_summary" in s:
        return "contract_summary"
    if "προσκληση" in s or s == "invitation":
        return "invitation"
    if (
        ("απευθειασ" in s and "αναθεσ" in s)
        or "πραξη αναθεσ" in s
        or "αναθεση προμηθειασ" in s
    ):
        return "award_decision"
    if "διαταγη διοικητου" in s or "διαταξη διοικητου" in s:
        return "administrative_order"
    # Unknown names are intentionally NOT forced into a category.
    return s


def normalized_value(field, value):
    """Field-aware normalization used for comparisons."""
    if field == "contractor_tax_id" and value is not None:
        return re.sub(r"\s|[-.]", "", str(value))
    if field == "document_type":
        return normalize_document_type(value)
    return normalized(value)