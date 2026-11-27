
import csv
import json
import re
import unicodedata
from pathlib import Path

import pymupdf


ANNOTATIONS = Path("data/annotations")
OUTPUT = Path("evaluation_results/annotation_audit_v1.csv")

PDF_MAP = {
    "doc_001": Path("data/raw/doc_1_digital.pdf"),
    "doc_002": Path("data/raw/doc_2_digital.pdf"),
    "doc_003": Path("data/raw/doc_3_digital.pdf"),
}


def normalize(text):
    text = unicodedata.normalize("NFC", str(text or ""))
    text = text.casefold()
    return re.sub(r"\s+", " ", text).strip()


def flatten_fields(data):
    """Support legacy and newer annotation structures."""

    if isinstance(data.get("fields"), dict):
        return data["fields"]

    fields = {}

    for group, group_data in data.items():
        if not isinstance(group_data, dict):
            continue

        for name, record in group_data.items():
            if isinstance(record, dict) and "status" in record:
                fields[f"{group}.{name}"] = record

    return fields


def evidence_details(record):
    evidence = record.get("evidence")

    if isinstance(evidence, dict):
        return evidence.get("text"), evidence.get("page")

    return evidence, None


def find_pdf(document_id):
    if document_id in PDF_MAP:
        return PDF_MAP[document_id]

    matches = list(Path("data").rglob(f"{document_id}.pdf"))
    return matches[0] if len(matches) == 1 else None


def audit_field(field_name, record, pages, scope_page):
    value = record.get("value")
    status = record.get("status")
    evidence, annotated_page = evidence_details(record)

    if annotated_page is None:
        annotated_page = scope_page

    row = {
        "field": field_name,
        "status": status,
        "value": value,
        "annotated_page": annotated_page,
        "matched_pages": "",
        "evidence_match": "not_checked",
        "issues": "",
        "human_review": "pending",
    }

    issues = []

    if status == "present":
        if value is None or not str(value).strip():
            issues.append("present_without_value")
        if not evidence or not str(evidence).strip():
            issues.append("present_without_evidence")

    elif status == "not_present":
        if value is not None:
            issues.append("not_present_with_value")
        if evidence is not None:
            issues.append("not_present_with_evidence")
        issues.append("absence_requires_scope_review")

    elif status == "uncertain":
        issues.append("uncertainty_requires_review")

    else:
        issues.append("invalid_or_missing_status")

    if pages is None:
        row["evidence_match"] = "pdf_unavailable"
        issues.append("pdf_unavailable")

    elif evidence and str(evidence).strip():
        needle = normalize(evidence)

        matched_pages = [
            number
            for number, text in pages.items()
            if needle in normalize(text)
        ]

        row["matched_pages"] = ",".join(
            map(str, matched_pages)
        )

        row["evidence_match"] = (
            "exact_normalized"
            if matched_pages
            else "not_found"
        )

        if not matched_pages:
            issues.append("evidence_not_found_in_text_layer")

        if annotated_page is not None:
            try:
                page_number = int(annotated_page)
                if page_number not in pages:
                    issues.append("invalid_annotated_page")
                elif matched_pages and page_number not in matched_pages:
                    issues.append("page_mismatch")
            except (ValueError, TypeError):
                issues.append("invalid_annotated_page")

        if annotated_page is None:
            issues.append("missing_page_attribution")

    row["issues"] = ";".join(issues)
    return row


def main():
    rows = []

    for annotation_path in sorted(ANNOTATIONS.glob("*.json")):
        data = json.loads(
            annotation_path.read_text(encoding="utf-8")
        )

        document_id = data.get(
            "document_id", annotation_path.stem
        )
        pdf_path = find_pdf(document_id)

        pages = None

        if pdf_path and pdf_path.exists():
            with pymupdf.open(pdf_path) as doc:
                pages = {
                    index + 1: page.get_text("text")
                    for index, page in enumerate(doc)
                }

        fields = flatten_fields(data)

        for field_name, record in fields.items():
            if not isinstance(record, dict):
                continue

            row = audit_field(
                field_name,
                record,
                pages,
                data.get("page_number"),
            )

            rows.append({
                "annotation": annotation_path.name,
                "document_id": document_id,
                "pdf": str(pdf_path) if pdf_path else "",
                **row,
            })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    columns = [
        "annotation",
        "document_id",
        "pdf",
        "field",
        "status",
        "value",
        "annotated_page",
        "matched_pages",
        "evidence_match",
        "issues",
        "human_review",
    ]

    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    print("Audit report:", OUTPUT)
    print("Fields examined:", len(rows))
    print("Evidence matches:", sum(
        row["evidence_match"] == "exact_normalized"
        for row in rows
    ))
    print("Human verification: NOT YET PERFORMED")


if __name__ == "__main__":
    main()
