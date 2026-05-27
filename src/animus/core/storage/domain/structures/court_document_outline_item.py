from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Integer, Text
from animus.core.storage.domain.structures.court_document_piece_kind import (
    CourtDocumentPieceKind,
)


@structure
class CourtDocumentOutlineItem(Structure):
    title: Text
    page_start: Integer
    kind: CourtDocumentPieceKind
    outline_index: Integer

    @classmethod
    def create(
        cls,
        title: str,
        page_start: int,
        kind: CourtDocumentPieceKind,
        outline_index: int,
    ) -> 'CourtDocumentOutlineItem':
        return cls(
            title=Text.create(title.strip()),
            page_start=Integer.create(page_start),
            kind=kind,
            outline_index=Integer.create(outline_index),
        )
