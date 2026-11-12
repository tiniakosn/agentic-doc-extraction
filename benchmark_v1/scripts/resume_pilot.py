
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from benchmark_v1.scripts.run_pilot import (
    load_cases,
    run_strategy,
)


SOURCE = Path(
    "evaluation_results/benchmark_v1/"
    "pilot_20261112T173144Z.json"
)

OUTPUT_DIR = Path("evaluation_results/benchmark_v1")
STRATEGIES = ("digital_llm", "direct_vlm")

MIN_INTERVAL_SEC = 65
MAX_ATTEMPTS = 3


def retry_delay(message):
    match = re.search(
        r"try again in\s+([\d.]+)s",
        message,
        flags=re.IGNORECASE,
    )

    return float(match.group(1)) + 3 if match else 65


def save(output, path):
    temporary = path.with_suffix(".tmp")

    temporary.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    temporary.replace(path)


def main():
    previous = json.loads(
        SOURCE.read_text(encoding="utf-8")
    )

    cases = load_cases()

    expected = {
        (case["annotation_id"], strategy)
        for case in cases
        for strategy in STRATEGIES
    }

    successful = {
        (record["annotation_id"], record["strategy"]): record
        for record in previous["results"]
        if record["status"] == "success"
        and (
            record["annotation_id"],
            record["strategy"],
        ) in expected
    }

    run_id = datetime.now(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ")

    path = OUTPUT_DIR / f"pilot_resumed_{run_id}.json"

    output = {
        "run_id": run_id,
        "source_run": str(SOURCE),
        "dataset": "pilot_development",
        "evaluation_unit": "page",
        "ground_truth_scoring": "disabled",
        "strategies": list(STRATEGIES),
        "results": list(successful.values()),
    }

    remaining = [
        (case, strategy)
        for case in cases
        for strategy in STRATEGIES
        if (case["annotation_id"], strategy)
        not in successful
    ]

    print("Reused successes:", len(successful))
    print("Remaining executions:", len(remaining))

    save(output, path)

    for case, strategy in remaining:
        key = (case["annotation_id"], strategy)

        for attempt in range(1, MAX_ATTEMPTS + 1):
            print(
                "Running:",
                key,
                f"attempt {attempt}",
                flush=True,
            )

            result = run_strategy(case, strategy)

            if result["status"] == "success":
                break

            error = result.get("error") or {}

            if error.get("type") != "RateLimitError":
                break

            if attempt == MAX_ATTEMPTS:
                break

            delay = max(
                MIN_INTERVAL_SEC,
                retry_delay(error.get("message", "")),
            )

            print(
                f"Rate limit: retry after {delay:.1f}s",
                flush=True,
            )
            time.sleep(delay)

        output["results"].append({
            **case,
            **result,
        })

        save(output, path)

        print(
            result["status"],
            result["latency_sec"],
            "sec",
            flush=True,
        )

        if result["status"] == "success":
            # Conservative pacing for the shared OTPM limit.
            time.sleep(MIN_INTERVAL_SEC)

    print("Saved:", path)
    print("Ground-truth accuracy: NOT CALCULATED")


if __name__ == "__main__":
    main()
