import json
from pathlib import Path

from benchmark_v1.scripts.evaluate_pilot import (
    build_report, check_afm, normalized_value, evidence_flags
)


def test_afm():
    assert check_afm("801033798") == "valid_checksum"
    assert check_afm("6983905183") == "invalid_format"


def test_normalization():
    assert normalized_value("issuing_authority", "ΠΡΩΤΟΔΙΚΕΙΟ ΚΟΡΙΝΘΟΥ") == normalized_value(
        "issuing_authority", "Πρωτοδικείο Κορίνθου")
    assert normalized_value("document_type", "Πράξη αναθέσεως") == "award_decision"
    assert normalized_value("document_type", "Απόφαση Ανάλυσης Υποχρέωσης") != "commitment_decision"


def test_evidence_warning():
    flags = evidence_flags("contractor_tax_id", "6983905183", "present", "ΑΦΜ: 6983905183")
    assert "afm_invalid_format" in flags


def test_pending_report(tmp_path):
    fields = {key: {"status": "not_present", "value": None, "evidence": []} for key in (
        "document_type", "issuing_authority", "recipient", "contractor", "contractor_tax_id")}
    ann = {"annotation_id": "case_1", "review": {"status": "pending"}, "fields": fields}
    (tmp_path / "case_1.json").write_text(json.dumps(ann), encoding="utf-8")
    preds = {"run_id": "synthetic", "results": [
        {"annotation_id": "case_1", "strategy": s, "status": "success", "prediction": fields}
        for s in ("digital_llm", "direct_vlm")
    ]}
    report = build_report(preds, tmp_path)
    assert not report["official_accuracy_computed"]
    assert report["annotation_counts"] == {"pending": 1}
    assert len(report["rows"]) == 10
    assert len(report["missing_or_failed"]) == 0


import pytest
from benchmark_v1.scripts.evaluate_pilot import normalize_document_type


@pytest.mark.parametrize(
    "raw_value, expected",
    [
        ("award_decision", "award_decision"),
        ("Απόφαση απευθείας ανάθεσης", "award_decision"),
        ("Απευθείας ανάθεση", "award_decision"),
        ("Πράξη αναθέσεως", "award_decision"),
        ("invitation", "invitation"),
        ("Πρόσκληση υποβολής προσφοράς", "invitation"),
        ("ΑΠΟΦΑΣΗ", "αποφαση"),
    ],
)
def test_document_type_normalization(raw_value, expected):
    assert normalize_document_type(raw_value) == expected
    