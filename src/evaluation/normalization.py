"""Exploratory, read-only Benchmark v1 evaluator; never calls an LLM API."""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

FIELDS = (
    "document_type", "issuing_authority", "recipient", "contractor", "contractor_tax_id"
)


def normalized(value):
    """Conservative normalization: accents/case/whitespace, not identity resolution."""
    if value is None:
        return None
    s = unicodedata.normalize("NFKC", str(value))
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    s = s.casefold()
    return " ".join(s.split())


def normalize_document_type(value):
    """Map only well-supported document-type synonyms; otherwise keep raw normalized value."""
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
    if field == "contractor_tax_id" and value is not None:
        return re.sub(r"\s|[-.]", "", str(value))
    if field == "document_type":
        return normalize_document_type(value)
    return normalized(value)


def check_afm(value):
    """Greek AFM checksum, 9 decimal digits (not proof of assignment/ownership)."""
    s = re.sub(r"\s|[-.]", "", str(value or ""))
    if not re.fullmatch(r"\d{9}", s):
        return "invalid_format"
    checksum = (sum(int(s[i]) * (2 ** (8 - i)) for i in range(8)) % 11) % 10
    return "valid_checksum" if checksum == int(s[-1]) else "invalid_checksum"


def extract_evidence_text(evidence):
    if isinstance(evidence, str):
        return evidence
    if isinstance(evidence, list):
        return " | ".join(extract_evidence_text(e) for e in evidence)
    if isinstance(evidence, dict):
        return str(evidence.get("text") or evidence.get("quote") or "")
    return ""


def evidence_flags(field, value, status, evidence):
    """Lightweight warnings; does not claim evidence is grounded in the PDF."""
    flags = []
    if status != "present":
        return flags
    text = extract_evidence_text(evidence)
    if not text.strip():
        flags.append("missing_evidence")
    if field == "contractor_tax_id":
        check = check_afm(value)
        if check != "valid_checksum":
            flags.append("afm_" + check)
        if text and str(value) not in text:
            flags.append("afm_not_in_model_evidence")
    return flags


def review_status(annotation):
    review = annotation.get("review", {})
    return str(review.get("status", "unknown")).strip().lower()


def build_report(prediction_data, annotation_dir):
    by_key = {}
    for r in prediction_data.get("results", []):
        key = (r.get("annotation_id"), r.get("strategy"))
        if key in by_key:
            raise ValueError(f"Duplicate run entry: {key}")
        by_key[key] = r

    entries = []
    missing = []
    annotation_paths = sorted(Path(annotation_dir).glob("*.json"))
    if not annotation_paths:
        raise ValueError(f"No annotation JSON files in {annotation_dir}")

    for path in annotation_paths:
        ann = json.loads(path.read_text(encoding="utf-8"))
        annotation_id = ann.get("annotation_id")
        if not annotation_id:
            raise ValueError(f"Missing annotation_id in {path}")
        status = review_status(ann)
        for strategy in ("digital_llm", "direct_vlm"):
            result = by_key.get((annotation_id, strategy))
            if not result or result.get("status") != "success":
                missing.append({"annotation_id": annotation_id, "strategy": strategy,
                                "reason": (result or {}).get("status", "missing")})
                continue
            prediction = result.get("prediction") or {}
            for field in FIELDS:
                a = ann.get("fields", {}).get(field)
                p = prediction.get(field)
                if not isinstance(a, dict) or not isinstance(p, dict):
                    missing.append({"annotation_id": annotation_id, "strategy": strategy,
                                    "reason": f"missing_field:{field}"})
                    continue
                a_status, p_status = a.get("status"), p.get("status")
                same_status = a_status == p_status
                a_norm = normalized_value(field, a.get("value"))
                p_norm = normalized_value(field, p.get("value"))
                same_value = a_norm == p_norm
                if not same_status:
                    category = "status_mismatch"
                elif a_status == "present" and not same_value:
                    category = "value_mismatch"
                elif a_status == "present":
                    category = "match"
                else:
                    category = "nonpresent_match" if same_value else "nonpresent_value_difference"
                flags = evidence_flags(field, p.get("value"), p_status, p.get("evidence"))
                entries.append({
                    "annotation_id": annotation_id, "strategy": strategy, "field": field,
                    "review_status": status, "category": category,
                    "reference_status": a_status, "reference_value": a.get("value"),
                    "prediction_status": p_status, "prediction_value": p.get("value"),
                    "prediction_evidence": extract_evidence_text(p.get("evidence")),
                    "evidence_flags": flags,
                })

    # IMPORTANT: all counts below are exploratory provisional-label comparisons.
    counts = {strategy: dict(Counter(e["category"] for e in entries if e["strategy"] == strategy))
              for strategy in ("digital_llm", "direct_vlm")}
    per_field = {}
    for strategy in ("digital_llm", "direct_vlm"):
        per_field[strategy] = {field: dict(Counter(e["category"] for e in entries
                          if e["strategy"] == strategy and e["field"] == field)) for field in FIELDS}
    return {
        "kind": "exploratory_provisional_annotation_comparison",
        "official_accuracy_computed": False,
        "note": "Pending/unverified annotations must not be called ground truth. "
                "Agreement does not imply correctness; evidence flags are heuristics, not PDF grounding.",
        "source_run_id": prediction_data.get("run_id"),
        "annotation_counts": dict(Counter(e["review_status"] for e in entries if e["strategy"] == "digital_llm" and e["field"] == FIELDS[0])),
        "summary_by_strategy": counts, "summary_by_field": per_field,
        "missing_or_failed": missing, "rows": entries,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--predictions", type=Path, required=True)
    ap.add_argument("--annotations", type=Path, default=Path("benchmark_v1/pilot_annotations"))
    ap.add_argument("--out", type=Path, default=Path("evaluation_results/benchmark_v1/evaluation_exploratory_v1"))
    args = ap.parse_args(argv)
    data = json.loads(args.predictions.read_text(encoding="utf-8"))
    report = build_report(data, args.annotations)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    json_path = args.out.with_suffix(".json")
    csv_path = args.out.with_suffix(".csv")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        columns = ["annotation_id", "strategy", "field", "review_status", "category",
                   "reference_status", "reference_value", "prediction_status", "prediction_value",
                   "prediction_evidence", "evidence_flags"]
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        for row in report["rows"]:
            writer.writerow({**row, "evidence_flags": ";".join(row["evidence_flags"])})
    print("EXPLORATORY ONLY | official ground-truth accuracy NOT computed")
    print("Review statuses:", report["annotation_counts"])
    for strategy, counts in report["summary_by_strategy"].items():
        print(strategy, counts)
    print("Missing/failed:", len(report["missing_or_failed"]))
    print("JSON:", json_path)
    print("CSV:", csv_path)


if __name__ == "__main__":
    main()
