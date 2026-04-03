from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.structures.dtos.analysis_petition_dto import (
    AnalysisPetitionDto,
)
from animus.core.intake.interfaces import (
    PetitionSummariesRepository,
    PetitionsRepository,
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
            petitions_repository: Annotated[
                PetitionsRepository,
                Depends(DatabasePipe.get_petitions_repository_from_request),
            ],
            petition_summaries_repository: Annotated[
                PetitionSummariesRepository,
                Depends(DatabasePipe.get_petition_summaries_repository_from_request),
            ],
        ) -> ListResponse[AnalysisPetitionDto]:
            use_case = ListAnalysisPetitionsUseCase(
                petitions_repository=petitions_repository,
                petition_summaries_repository=petition_summaries_repository,
            )

            return use_case.execute(analysis.id.value)
