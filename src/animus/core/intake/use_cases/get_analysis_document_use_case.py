from animus.core.intake.domain.errors import AnalysisDocumentNotFoundError
from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.interfaces import AnalysisDocumentsRepository
from animus.core.shared.domain.structures import Id


class GetAnalysisDocumentUseCase:
    def __init__(
        self, analysis_documents_repository: AnalysisDocumentsRepository
    ) -> None:
        self._analysis_documents_repository = analysis_documents_repository

    def execute(self, analysis_id: str) -> AnalysisDocumentDto:
        analysis_id_entity = Id.create(analysis_id)
        analysis_document = self._analysis_documents_repository.find_by_analysis_id(
            analysis_id=analysis_id_entity,
        )

        if analysis_document is None:
            raise AnalysisDocumentNotFoundError

        return analysis_document.dto
