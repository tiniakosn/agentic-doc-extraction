import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq


def get_llm(model_name: str = "qwen/qwen3.8-27b") -> ChatGroq:
    """Create a Groq chat model for the active workflow."""

    load_dotenv()

    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("Missing GROQ_API_KEY")

    return ChatGroq(
        model=model_name,
        temperature=0,
    )