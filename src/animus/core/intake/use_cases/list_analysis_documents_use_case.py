from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.interfaces import AnalysisDocumentsRepository
from animus.core.shared.domain.structures import Id


class ListAnalysisDocumentsUseCase:
    def __init__(
        self, analysis_documents_repository: AnalysisDocumentsRepository
    ) -> None:
        self._analysis_documents_repository = analysis_documents_repository

    def execute(self, analysis_id: str) -> list[AnalysisDocumentDto]:
        analysis_id_entity = Id.create(analysis_id)
        analysis_documents = (
            self._analysis_documents_repository.find_many_by_analysis_id(
                analysis_id=analysis_id_entity,
            )
        )

        return [analysis_document.dto for analysis_document in analysis_documents]
