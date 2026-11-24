
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq


DEFAULT_MODEL = "qwen/qwen3.8-27b"


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
