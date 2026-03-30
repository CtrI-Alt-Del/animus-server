from typing import Protocol

from animus.core.shared.domain.structures import Text
from animus.core.storage.domain.structures import File


class PdfProvider(Protocol):
    def extract_content(self, pdf_file: File) -> Text: ...
