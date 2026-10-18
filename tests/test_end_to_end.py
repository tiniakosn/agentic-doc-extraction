import json
import time
from pathlib import Path
from src.utils.pdf_loader import load_pdf_document
from src.graph import app
from src.schemas.state import ExtractionState

DOCUMENTS = [
    "data/raw/doc_1_digital.pdf",
    "data/raw/doc_2_digital.pdf",
    "data/raw/doc_3_digital.pdf",
    "data/raw/doc_4_scanned.pdf",
]


def evaluate_all():
    results_summary = []
    output_dir = Path("evaluation_results")
    output_dir.mkdir(exist_ok=True)

    print("==================================================")
    print("      ΕΚΚΙΝΗΣΗ PIPELINE BENCHMARK & METRICS      ")
    print("==================================================")

    for doc_path_str in DOCUMENTS:
        path = Path(doc_path_str)
        if not path.exists():
            print(f"[SKIP] Το αρχείο {path.name} δεν βρέθηκε.")
            continue

        print(f"\n>>> Επεξεργασία: {path.name}")
        text, metadata = load_pdf_document(path)
        ada = metadata.get("ada") or path.stem

        # Μοναδικό session thread ανά έγγραφο για το SQLite Checkpointing
        config = {"configurable": {"thread_id": f"benchmark_{path.stem}"}}

        initial_state: ExtractionState = {
            "document_text": text,
            "pdf_metadata": metadata,
            "extracted_data": None,
            "validation_errors": [],
            "feedback_message": None,
            "retry_count": 0,
            "max_retries": 3,
            "is_valid": False,
            "audit_log": [],
            "metrics": {},
        }

        total_start = time.time()
        final_state = app.invoke(initial_state, config=config)
        total_duration = round(time.time() - total_start, 2)

        final_metrics = final_state.get("metrics", {})
        final_metrics["total_duration_sec"] = total_duration

        is_valid = final_state.get("is_valid", False)
        retries = final_state.get("retry_count", 0)

        record = {
            "document": path.name,
            "track": metadata.get("track"),
            "ada": metadata.get("ada"),
            "text_length": len(text),
            "is_valid": is_valid,
            "retries_count": retries,
            "metrics": final_metrics,
            "audit_trail": final_state.get("audit_log", []),
            "extracted_data": final_state.get("extracted_data"),
            "errors": final_state.get("validation_errors", []),
        }
        results_summary.append(record)

        status_str = "ΕΠΙΤΥΧΙΑ (Valid)" if is_valid else "ΑΠΟΤΥΧΙΑ (Invalid)"
        print(f"    Track: {metadata.get('track')} | Αποτέλεσμα: {status_str}")
        print(f"    Χρόνος: {total_duration}s | Retries: {retries}")

    # Αποθήκευση Benchmark Report
    report_file = output_dir / "benchmark_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Το πλήρες Benchmark Report αποθηκεύτηκε στο: {report_file}")


if __name__ == "__main__":
    evaluate_all()