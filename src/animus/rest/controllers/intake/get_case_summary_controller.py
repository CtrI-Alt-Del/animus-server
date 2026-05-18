from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.structures.dtos.case_summary_dto import CaseSummaryDto
from animus.core.intake.interfaces import CaseSummariesRepository
from animus.core.intake.use_cases import GetCaseSummaryUseCase
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe


class GetCaseSummaryController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/analyses/{analysis_id}/case-summaries',
            status_code=200,
            response_model=CaseSummaryDto,
        )
        def _(
            analysis: Annotated[
                Analysis,
                Depends(IntakePipe.verify_analysis_by_account_from_request),
            ],
            case_summaries_repository: Annotated[
                CaseSummariesRepository,
                Depends(DatabasePipe.get_case_summaries_repository_from_request),
            ],
        ) -> CaseSummaryDto:
            use_case = GetCaseSummaryUseCase(
                case_summaries_repository=case_summaries_repository,
            )

            return use_case.execute(analysis_id=analysis.id.value)
