from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.structures.dtos import AnalysisPrecedentDto
from animus.core.intake.interfaces import AnalysisPrecedentsRepository
from animus.core.intake.use_cases import ListAnalysisPrecedentsUseCase
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe


class ListAnalysisPrecedentsController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/analyses/{analysis_id}/precedents',
            status_code=200,
            response_model=list[AnalysisPrecedentDto],
        )
        def _(
            analysis: Annotated[
                Analysis,
                Depends(IntakePipe.verify_analysis_by_account_from_request),
            ],
            analysis_precedents_repository: Annotated[
                AnalysisPrecedentsRepository,
                Depends(DatabasePipe.get_analysis_precedents_repository_from_request),
            ],
        ) -> list[AnalysisPrecedentDto]:
            use_case = ListAnalysisPrecedentsUseCase(
                analysis_precedents_repository=analysis_precedents_repository,
            )

            return use_case.execute(analysis_id=analysis.id.value)
