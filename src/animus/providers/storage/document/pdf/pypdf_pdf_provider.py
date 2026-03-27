from io import BytesIO

from pypdf import PdfReader

from animus.core.shared.domain.structures import Text
from animus.core.storage.domain.structures import File
from animus.core.storage.interfaces import PdfProvider


class PypdfPdfProvider(PdfProvider):
    def extract_content(self, pdf_file: File) -> Text:
        reader = PdfReader(BytesIO(pdf_file.value))
        pages_content = [page.extract_text() or '' for page in reader.pages]
        content = '\n'.join(pages_content).strip()

        return Text.create(content)
