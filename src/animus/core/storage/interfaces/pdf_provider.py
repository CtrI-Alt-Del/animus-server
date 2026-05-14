from typing import Protocol

from animus.core.shared.domain.structures import Integer, Text
from animus.core.storage.domain.structures import File


class PdfProvider(Protocol):
    def count_pages(self, pdf_file: File) -> Integer: ...

    def extract_pages(self, pdf_file: File, start: Integer, end: Integer) -> Text: ...

    def extract_content(self, pdf_file: File) -> Text: ...
