from pathlib import Path
from typing import Protocol

from src.schemas.document import TextLayer


class PageProcessor(Protocol):
    def process_page(
        self,
        pdf_path: str | Path,
        page_number: int,
    ) -> TextLayer:
        ...