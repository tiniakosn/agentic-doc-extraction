
from unittest.mock import patch

import pytest

from src.extraction.llm_client import get_llm


def test_llm_client_uses_default_configuration():
    with (
        patch("src.extraction.llm_client.load_dotenv"),
        patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}),
        patch("src.extraction.llm_client.ChatGroq") as mock_groq,
    ):
        get_llm()

    mock_groq.assert_called_once_with(
        model="qwen/qwen3.8-27b",
        temperature=0,
    )


def test_llm_client_preserves_explicit_retry_configuration():
    with (
        patch("src.extraction.llm_client.load_dotenv"),
        patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}),
        patch("src.extraction.llm_client.ChatGroq") as mock_groq,
    ):
        get_llm(
            model_name="qwen/qwen3.8-27b",
            temperature=0,
            max_retries=0,
        )

    mock_groq.assert_called_once_with(
        model="qwen/qwen3.8-27b",
        temperature=0,
        max_retries=0,
    )


def test_llm_client_requires_api_key():
    with (
        patch("src.extraction.llm_client.load_dotenv"),
        patch.dict("os.environ", {}, clear=True),
    ):
        with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
            get_llm()
