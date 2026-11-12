#!/usr/bin/env python3
"""Validate Benchmark v1 annotation structure; never auto-verify records."""
import argparse
import json
from pathlib import Path

FIELDS = {"document_type", "issuing_authority", "recipient", "contractor", "contractor_tax_id"}
STATUSES = {"present", "not_present", "uncertain"}
REVIEW = {"pending", "verified", "rejected"}
ROLES = {"awarded_total_amount", "estimated_budget", "unit_rate", "performance_guarantee", "vat_rate"}


def check(data):
    errors = []
    def require(cond, msg):
        if not cond:
            errors.append(msg)

    require(data.get("schema_version") == "1.0", "schema_version must be 1.0")
    doc = data.get("document") or {}
    require(bool(doc.get("document_id")), "document.document_id required")
    require(bool(doc.get("pdf_path")), "document.pdf_path required")
    require(doc.get("split") in {"dev", "test"}, "document.split must be dev/test")
    require(data.get("scope") in {"page", "document"}, "scope must be page/document")
    if data.get("scope") == "page":
        require(isinstance(data.get("page_number"), int) and data["page_number"] > 0, "page scope requires positive page_number")
    else:
        require(data.get("page_number") is None, "document scope requires null page_number")

    fields = data.get("fields") or {}
    require(set(fields) == FIELDS, "fields must contain exactly the five primary fields")
    for name in FIELDS & set(fields):
        f = fields[name]
        if not isinstance(f, dict):
            errors.append(f"{name}: expected object")
            continue
        status, value, evidence = f.get("status"), f.get("value"), f.get("evidence")
        require(status in STATUSES, f"{name}: invalid status")
        require(isinstance(evidence, list), f"{name}: evidence must be list")
        if status == "present":
            require(isinstance(value, str) and bool(value.strip()), f"{name}: present requires nonempty string value")
            require(isinstance(evidence, list) and len(evidence) > 0, f"{name}: present requires evidence")
        else:
            require(value is None, f"{name}: {status} requires null value")
            if status == "not_present":
                require(evidence == [], f"{name}: not_present requires empty evidence")
        for i, item in enumerate(evidence if isinstance(evidence, list) else []):
            require(isinstance(item, dict) and isinstance(item.get("page"), int) and item["page"] > 0, f"{name}.evidence[{i}]: positive page required")
            require(isinstance(item, dict) and isinstance(item.get("text"), str) and bool(item["text"].strip()), f"{name}.evidence[{i}]: text required")
            require(isinstance(item, dict) and item.get("source_kind") in {"digital", "ocr", "visual"}, f"{name}.evidence[{i}]: source_kind required")
            if isinstance(item, dict) and isinstance(item.get("page"), int):
                if data.get("scope") == "page":
                    require(item["page"] == data.get("page_number"), f"{name}.evidence[{i}]: page outside scope")
                if isinstance(doc.get("page_count"), int):
                    require(item["page"] <= doc["page_count"], f"{name}.evidence[{i}]: page outside PDF")

    observations = data.get("financial_observations", [])
    require(isinstance(observations, list), "financial_observations must be list")
    if isinstance(observations, list):
        for i, item in enumerate(observations):
            require(isinstance(item, dict) and item.get("role") in ROLES, f"financial_observations[{i}]: invalid role")
            require(isinstance(item, dict) and isinstance(item.get("amount"), str), f"financial_observations[{i}]: decimal amount string required")
            if isinstance(item, dict) and isinstance(item.get("amount"), str):
                try:
                    from decimal import Decimal
                    Decimal(item["amount"])
                except Exception:
                    errors.append(f"financial_observations[{i}]: invalid decimal")
            require(isinstance(item, dict) and isinstance(item.get("evidence"), list) and bool(item["evidence"]), f"financial_observations[{i}]: evidence required")

    review = data.get("review") or {}
    require(review.get("status") in REVIEW, "review.status invalid")
    if review.get("status") == "verified":
        require(bool(review.get("reviewer")), "verified requires reviewer")
        require(bool(review.get("reviewed_at")), "verified requires reviewed_at")
        require(isinstance(doc.get("sha256"), str) and len(doc["sha256"]) == 64, "verified requires SHA-256")
        require(isinstance(doc.get("page_count"), int) and doc["page_count"] > 0, "verified requires page_count")
        require(all(f.get("status") != "uncertain" for f in fields.values() if isinstance(f, dict)), "verified record has unresolved uncertain fields; adjudicate or record in pending")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    failed = 0
    for path in args.paths:
        try:
            errors = check(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError) as exc:
            errors = [str(exc)]
        print(f"{'PASS' if not errors else 'FAIL'}: {path}")
        for error in errors:
            print(f"  - {error}")
        failed += bool(errors)
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
