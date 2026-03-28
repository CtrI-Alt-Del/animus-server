from typing import Protocol

from animus.core.shared.domain.structures import Text
from animus.core.storage.domain.structures import File


class DocxProvider(Protocol):
    def extract_content(self, docx_file: File) -> Text: ...
