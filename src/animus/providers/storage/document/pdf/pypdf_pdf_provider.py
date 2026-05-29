from io import BytesIO
from typing import cast

from pypdf import PdfReader
from pypdf.generic import Destination

from animus.core.shared.domain.structures import Integer, Text
from animus.core.storage.domain.structures import File, PdfOutlineItem
from animus.core.storage.interfaces import PdfProvider


class PypdfPdfProvider(PdfProvider):
    def count_pages(self, pdf_file: File) -> Integer:
        reader = PdfReader(BytesIO(pdf_file.value))
        return Integer.create(len(reader.pages))

    def extract_outline(self, pdf_file: File) -> list[PdfOutlineItem]:
        reader = PdfReader(BytesIO(pdf_file.value))
        outline_items: list[PdfOutlineItem] = []

        def collect(items: object) -> None:
            if not isinstance(items, list):
                return

            for item in cast('list[object]', items):
                if isinstance(item, list):
                    collect(cast('object', item))
                    continue

                if not isinstance(item, Destination):
                    continue

                title = item.title.strip() if item.title is not None else ''
                if not title:
                    continue

                page_number = reader.get_destination_page_number(item)
                if page_number is None or page_number < 0:
                    continue

                outline_items.append(
                    PdfOutlineItem.create(title=title, page_number=page_number + 1)
                )

        collect(cast('object', reader.outline))

        return outline_items

    def extract_pages(self, pdf_file: File, start: Integer, end: Integer) -> Text:
        reader = PdfReader(BytesIO(pdf_file.value))
        pages_content = [
            page.extract_text() or ''
            for page in reader.pages[start.value - 1 : end.value]
        ]
        content = '\n'.join(pages_content).strip()

        return Text.create(content)

    def extract_content(self, pdf_file: File) -> Text:
        reader = PdfReader(BytesIO(pdf_file.value))
        pages_content = [page.extract_text() or '' for page in reader.pages]
        content = '\n'.join(pages_content).strip()

        return Text.create(content)
