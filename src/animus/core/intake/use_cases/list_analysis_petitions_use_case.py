from animus.core.intake.domain.structures.dtos.analysis_petition_dto import (
    AnalysisPetitionDto,
)
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    CaseSummariesRepository,
)
from animus.core.shared.domain.structures import Id
from animus.core.shared.responses import ListResponse


class ListAnalysisPetitionsUseCase:
    def __init__(
        self,
        analysis_documents_repository: AnalysisDocumentsRepository,
        case_summaries_repository: CaseSummariesRepository,
    ) -> None:
        self._analysis_documents_repository = analysis_documents_repository
        self._case_summaries_repository = case_summaries_repository

    def execute(self, analysis_id: str) -> ListResponse[AnalysisPetitionDto]:
        analysis_id_entity = Id.create(analysis_id)
        document = self._analysis_documents_repository.find_by_analysis_id(
            analysis_id=analysis_id_entity,
        )
        if document is None:
            return ListResponse(items=[])

        case_summary = self._case_summaries_repository.find_by_analysis_id(
            analysis_id=analysis_id_entity,
        )

        return ListResponse(
            items=[
                AnalysisPetitionDto(
                    document=document.dto,
                    case_summary=case_summary.dto if case_summary is not None else None,
                )
            ]
        )
