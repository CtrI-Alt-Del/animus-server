from typing import Protocol

from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.domain.structures.petition_draft import PetitionDraft


class PetitionDraftDocxProvider(Protocol):
    def export(
        self,
        analysis_id: str,
        analysis_name: str,
        petition_draft: PetitionDraft,
    ) -> AnalysisDocumentDto: ...
