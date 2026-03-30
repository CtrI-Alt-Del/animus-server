from io import BytesIO

from docx import Document

from animus.core.shared.domain.structures import Text
from animus.core.storage.domain.structures import File
from animus.core.storage.interfaces import DocxProvider


class PythonDocxProvider(DocxProvider):
    def extract_content(self, docx_file: File) -> Text:
        document = Document(BytesIO(docx_file.value))
        paragraphs_content = [paragraph.text for paragraph in document.paragraphs]
        content = '\n'.join(paragraphs_content).strip()

        return Text.create(content)
