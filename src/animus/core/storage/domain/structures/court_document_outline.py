import unicodedata

from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.storage.domain.errors import InsufficientCourtDocumentError
from animus.core.storage.domain.structures.court_document_outline_item import (
    CourtDocumentOutlineItem,
)
from animus.core.storage.domain.structures.court_document_piece_kind import (
    CourtDocumentPieceKind,
)
from animus.core.storage.domain.structures.pdf_outline_item import PdfOutlineItem


@structure
class CourtDocumentOutline(Structure):
    items: list[CourtDocumentOutlineItem]

    @classmethod
    def create_from_pdf_outline_items(
        cls, pdf_outline_items: list[PdfOutlineItem]
    ) -> 'CourtDocumentOutline':
        items = [
            CourtDocumentOutlineItem.create(
                title=pdf_outline_item.title.value,
                page_start=pdf_outline_item.page_number.value,
                kind=kind,
                outline_index=outline_index,
            )
            for outline_index, pdf_outline_item in enumerate(pdf_outline_items)
            if (kind := cls._classify(pdf_outline_item.title.value)) is not None
        ]

        outline = cls(items=items)

        if not outline.has_required_pieces():
            raise InsufficientCourtDocumentError

        return outline

    def find_sentencas(self) -> list[CourtDocumentOutlineItem]:
        return sorted(
            [
                item
                for item in self.items
                if item.kind == CourtDocumentPieceKind.SENTENCA
            ],
            key=lambda item: item.page_start.value,
        )

    def find_apelacoes(self) -> list[CourtDocumentOutlineItem]:
        apelacoes = [
            item for item in self.items if item.kind == CourtDocumentPieceKind.APELACAO
        ]
        apelacoes_em_pdf = [
            item
            for item in apelacoes
            if 'apelacao em pdf'
            in self._normalize_title(item.title.value)  # fix: era 'apelação em pdf'
        ]
        selected_apelacoes = apelacoes_em_pdf or apelacoes

        return sorted(selected_apelacoes, key=lambda item: item.page_start.value)

    def find_contrarrazoes(self) -> list[CourtDocumentOutlineItem]:
        return sorted(
            [
                item
                for item in self.items
                if item.kind == CourtDocumentPieceKind.CONTRARRAZOES
            ],
            key=lambda item: item.page_start.value,
        )

    def has_required_pieces(self) -> bool:
        return bool(self.find_sentencas()) and bool(self.find_apelacoes())

    @classmethod
    def _classify(cls, title: str) -> CourtDocumentPieceKind | None:
        normalized_title = cls._normalize_title(title)

        if 'sentenca' in normalized_title:
            return CourtDocumentPieceKind.SENTENCA

        if 'apelacao em pdf' in normalized_title:  # fix: era 'apelação em pdf'
            return CourtDocumentPieceKind.APELACAO

        if 'apelacao' in normalized_title:  # fix: era 'apelação'
            return CourtDocumentPieceKind.APELACAO

        if 'contrarrazoes' in normalized_title or 'contra-razoes' in normalized_title:
            return CourtDocumentPieceKind.CONTRARRAZOES

        return None

    @staticmethod
    def _normalize_title(title: str) -> str:
        return ''.join(
            char
            for char in unicodedata.normalize('NFD', title.casefold().strip())
            if unicodedata.category(char) != 'Mn'
        )
