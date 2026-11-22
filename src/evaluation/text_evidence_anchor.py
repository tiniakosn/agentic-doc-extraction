import re

def find_text_anchor(
    value: str,
    source_text: str,
    context_chars: int = 0,
) -> dict | None:
    """Find source text while preserving original character offsets."""

    if not value or not source_text:
        return None

    if context_chars < 0:
        raise ValueError("context_chars must be non-negative")

    tokens = value.split()

    if not tokens:
        return None

    pattern = r"\s+".join(
        re.escape(token)
        for token in tokens
    )

    match = re.search(pattern, source_text)

    if match is None:
        return None

    start = match.start()
    end = match.end()

    context_start = max(0, start - context_chars)
    context_end = min(
        len(source_text),
        end + context_chars,
    )

    return {
        "text": source_text[start:end],
        "start": start,
        "end": end,
        "context": source_text[context_start:context_end],
        "context_start": context_start,
        "context_end": context_end,
    }