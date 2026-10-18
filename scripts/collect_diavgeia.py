
import argparse
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pymupdf
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


API_BASE = "https://diavgeia.gov.gr/opendata"
PDF_DIR = Path("data/discovery")
METADATA_DIR = Path("data/metadata")

logger = logging.getLogger("diavgeia_collector")


def create_session():
    """Create an HTTP session with bounded retries."""
    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "User-Agent": "MSc-DocumentResearch/0.2",
    })

    retries = Retry(
        total=3,
        connect=3,
        read=2,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    return session


def fetch_metadata(session, ada):
    """Retrieve official metadata for one decision."""
    response = session.get(
        f"{API_BASE}/decisions/{ada}",
        timeout=(10, 30),
    )
    response.raise_for_status()

    decision = response.json()

    if decision.get("ada") != ada:
        raise ValueError(f"ADA mismatch for {ada}")

    return decision


def search_decisions(
    session,
    decision_type="Δ.1",
    size=5,
    page=0,
    from_date=None,
    to_date=None,
):
    params = {
        "type": decision_type,
        "size": size,
        "page": page,
    }

    if from_date:
        params["from_issue_date"] = from_date

    if to_date:
        params["to_issue_date"] = to_date

    response = session.get(
        f"{API_BASE}/search",
        params=params,
        timeout=(10, 30),
    )
    response.raise_for_status()

    return response.json().get("decisions", [])


def inspect_pdf(pdf_bytes):
    """Validate PDF bytes and return technical metadata."""
    if not pdf_bytes.startswith(b"%PDF-"):
        raise ValueError("Invalid PDF signature")

    with pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf",
    ) as document:
        if document.needs_pass:
            raise ValueError("Password-protected PDF")

        page_count = len(document)

        if page_count == 0:
            raise ValueError("PDF contains no pages")

    return {
        "pdf_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        "pdf_size_bytes": len(pdf_bytes),
        "page_count": page_count,
    }


def atomic_write(path, content):
    """Write through a temporary file to avoid partial output."""
    temporary = path.with_name(path.name + ".tmp")

    try:
        with temporary.open("wb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def collect_decision(session, ada):
    """Collect or repair one PDF and its metadata."""
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    pdf_path = PDF_DIR / f"{ada}.pdf"
    metadata_path = METADATA_DIR / f"{ada}.json"

    decision = fetch_metadata(session, ada)

    # Reuse an existing valid PDF.
    if pdf_path.exists():
        pdf_bytes = pdf_path.read_bytes()

        try:
            technical = inspect_pdf(pdf_bytes)
        except (ValueError, RuntimeError):
            logger.warning("Invalid cached PDF: %s", ada)
            pdf_bytes = None
    else:
        pdf_bytes = None

    # Download only when the PDF is missing or invalid.
    if pdf_bytes is None:
        document_url = decision.get("documentUrl")

        if not document_url:
            raise ValueError(f"Missing documentUrl: {ada}")

        if not document_url.startswith(
            "https://diavgeia.gov.gr/doc/"
        ):
            raise ValueError(f"Unexpected document URL: {ada}")

        response = session.get(
            document_url,
            timeout=(10, 90),
        )
        response.raise_for_status()

        pdf_bytes = response.content
        technical = inspect_pdf(pdf_bytes)

        atomic_write(pdf_path, pdf_bytes)
        logger.info("Downloaded PDF: %s", ada)

    # Preserve the original collection timestamp when available.
    previous = {}
    if metadata_path.exists():
        try:
            previous = json.loads(
                metadata_path.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError):
            logger.warning("Repairing metadata: %s", ada)

    metadata = {
        "source": "diavgeia",
        "ada": ada,
        "collected_at": previous.get("collected_at"),
        "metadata_updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        **technical,
        "decision": decision,
    }

    # The original collection time is unknown for legacy files.
    if not pdf_path.exists():
        raise RuntimeError(f"PDF missing after collection: {ada}")

    if metadata["collected_at"] is None and previous == {}:
        metadata["collection_time_verified"] = False

    atomic_write(
        metadata_path,
        json.dumps(
            metadata,
            ensure_ascii=False,
            indent=2,
        ).encode("utf-8"),
    )

    logger.info(
        "[OK] %s | %s pages | %s",
        ada,
        technical["page_count"],
        technical["pdf_sha256"][:12],
    )

    return metadata


def main():
    parser = argparse.ArgumentParser(
        description="Diavgeia research document collector"
    )
    parser.add_argument("--ada", help="Collect a specific ADA")
    parser.add_argument("--type", default="Δ.1")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--page", type=int, default=0)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--from-date")
    parser.add_argument("--to-date")

    args = parser.parse_args()

    if not 1 <= args.limit <= 100:
        parser.error("--limit must be between 1 and 100")
    if args.delay < 0.5:
        parser.error("--delay must be at least 0.5 seconds")
    if args.page < 0:
        parser.error("--page must be non-negative")

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    with create_session() as session:
        if args.ada:
            adas = [args.ada]
        else:
            decisions = search_decisions(
                session,
                decision_type=args.type,
                size=args.limit,
                page=args.page,
                from_date=args.from_date,
                to_date=args.to_date,
            )
            adas = list(dict.fromkeys(
                d["ada"] for d in decisions
            ))

        succeeded = 0
        failed = 0

        for index, ada in enumerate(adas):
            try:
                collect_decision(session, ada)
                succeeded += 1
            except (requests.RequestException, ValueError,
                    RuntimeError, OSError) as error:
                failed += 1
                logger.error("[FAIL] %s: %s", ada, error)

            if index < len(adas) - 1:
                time.sleep(args.delay)

        logger.info(
            "Finished | success=%s | failed=%s",
            succeeded,
            failed,
        )

        if failed:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
