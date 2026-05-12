from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.structures.dtos.analysis_petition_dto import (
    AnalysisPetitionDto,
)
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    CaseSummariesRepository,
)
from animus.core.intake.use_cases import ListAnalysisPetitionsUseCase
from animus.core.shared.responses import ListResponse
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe


class ListAnalysisPetitionsController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/analyses/{analysis_id}/petitions',
            status_code=200,
            response_model=ListResponse[AnalysisPetitionDto],
        )
        def _(
            analysis: Annotated[
                Analysis,
                Depends(IntakePipe.verify_analysis_by_account_from_request),
            ],
            analysis_documents_repository: Annotated[
                AnalysisDocumentsRepository,
                Depends(DatabasePipe.get_analysis_documents_repository_from_request),
            ],
            case_summaries_repository: Annotated[
                CaseSummariesRepository,
                Depends(DatabasePipe.get_case_summaries_repository_from_request),
            ],
        ) -> ListResponse[AnalysisPetitionDto]:
            use_case = ListAnalysisPetitionsUseCase(
                analysis_documents_repository=analysis_documents_repository,
                case_summaries_repository=case_summaries_repository,
            )

            return use_case.execute(analysis.id.value)
