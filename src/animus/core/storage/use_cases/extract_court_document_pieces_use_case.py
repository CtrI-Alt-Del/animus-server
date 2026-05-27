from animus.core.shared.domain.structures import Decimal, Integer, Text
from animus.core.storage.domain.errors import CourtDocumentIndexNotFoundError
from animus.core.storage.domain.structures import (
    CourtDocumentOutline,
    CourtDocumentOutlineItem,
    ExtractedCourtDocumentPieces,
    File,
    PdfOutlineItem,
)
from animus.core.storage.domain.structures.dtos import FileDto
from animus.core.storage.interfaces.pdf_provider import PdfProvider


class ExtractCourtDocumentPiecesUseCase:
    def __init__(self, pdf_provider: PdfProvider) -> None:
        self._pdf_provider = pdf_provider

    def execute(self, pdf_file: FileDto) -> ExtractedCourtDocumentPieces:
        file = self._to_file(pdf_file)
        pdf_outline_items = self._pdf_provider.extract_outline(file)
        if not pdf_outline_items:
            raise CourtDocumentIndexNotFoundError
        
        court_document_outline = CourtDocumentOutline.create_from_pdf_outline_items(
            pdf_outline_items
        )
        total_pages = self._pdf_provider.count_pages(file)

        sentenca = self._extract_many(
            pdf_file=file,
            pieces=court_document_outline.find_sentencas(),
            pdf_outline_items=pdf_outline_items,
            total_pages=total_pages,
        )
        apelacao = self._extract_many(
            pdf_file=file,
            pieces=court_document_outline.find_apelacoes(),
            pdf_outline_items=pdf_outline_items,
            total_pages=total_pages,
        )

        contrarrazoes_pieces = court_document_outline.find_contrarrazoes()
        contrarrazoes = (
            self._extract_many(
                pdf_file=file,
                pieces=contrarrazoes_pieces,
                pdf_outline_items=pdf_outline_items,
                total_pages=total_pages,
            ).value
            if contrarrazoes_pieces
            else None
        )
        
        return ExtractedCourtDocumentPieces.create(
            sentenca=sentenca.value,
            apelacao=apelacao.value,
            contrarrazoes=contrarrazoes,
        )

    def _to_file(self, pdf_file: FileDto) -> File:
        return File.create(
            value=pdf_file.value,
            key=Text.create(pdf_file.key),
            size_in_bytes=Decimal.create(pdf_file.size_in_bytes),
            mime_type=Text.create(pdf_file.mime_type),
        )

    def _extract_many(
        self,
        pdf_file: File,
        pieces: list[CourtDocumentOutlineItem],
        pdf_outline_items: list[PdfOutlineItem],
        total_pages: Integer,
    ) -> Text:
        return Text.create(
            '\n\n'.join(
                self._pdf_provider.extract_pages(
                    pdf_file=pdf_file,
                    start=piece.page_start,
                    end=self._find_ceiling(
                        item=piece,
                        pdf_outline_items=pdf_outline_items,
                        total_pages=total_pages,
                    ),
                ).value
                for piece in pieces
            )
        )

    def _find_ceiling(
        self,
        item: CourtDocumentOutlineItem,
        pdf_outline_items: list[PdfOutlineItem],
        total_pages: Integer,
    ) -> Integer:
        next_outline_index = item.outline_index.value + 1
        if next_outline_index >= len(pdf_outline_items):
            return total_pages

        next_page_number = pdf_outline_items[next_outline_index].page_number.value - 1
        return Integer.create(max(item.page_start.value, next_page_number))
