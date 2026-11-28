import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq


DEFAULT_MODEL = "qwen/qwen3.8-27b"

USAGE_LOG = Path(
    os.getenv("TOKEN_USAGE_LOG", "evaluation_results/token_usage.jsonl")
)


def get_llm(
    model_name: str = DEFAULT_MODEL,
    *,
    temperature: float = 0,
    max_retries: int | None = None,
) -> ChatGroq:
    """Create a centrally configured Groq chat model."""

    load_dotenv()

    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("Missing GROQ_API_KEY")

    config = {
        "model": model_name,
        "temperature": temperature,
    }

    # Preserve the provider's default retry policy unless overridden.
    if max_retries is not None:
        config["max_retries"] = max_retries

    return ChatGroq(**config)


def log_usage(
    raw,
    *,
    call_type: str,
    model: str,
    latency_s: float | None = None,
    extra: dict | None = None,
) -> dict:
    """Append token usage of one LLM call to a JSONL log."""

    usage = getattr(raw, "usage_metadata", None) or {}

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "call_type": call_type,
        "model": model,
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "latency_s": round(latency_s, 3) if latency_s is not None else None,
    }
    if extra:
        record.update(extra)

    try:
        USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with USAGE_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass  # Logging must never break extraction.

    return record


def unwrap_structured(
    result,
    schema,
    *,
    call_type: str,
    model: str,
    latency_s: float | None = None,
    extra: dict | None = None,
):
    """Handle include_raw=True output: log usage, return parsed schema."""

    if isinstance(result, dict) and "parsed" in result:
        log_usage(
            result.get("raw"),
            call_type=call_type,
            model=model,
            latency_s=latency_s,
            extra=extra,
        )
        if result.get("parsing_error") is not None:
            raise result["parsing_error"]
        result = result["parsed"]

    if isinstance(result, schema):
        return result

    return schema.model_validate(result)