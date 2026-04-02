from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.entities.dtos.petition_dto import PetitionDto
from animus.core.intake.interfaces import PetitionsRepository
from animus.core.intake.use_cases import GetAnalysisPetitionUseCase
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe


class GetAnalysisPetitionController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/analyses/{analysis_id}/petition',
            status_code=200,
            response_model=PetitionDto,
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
        ) -> PetitionDto:
            use_case = GetAnalysisPetitionUseCase(
                petitions_repository=petitions_repository,
            )

            return use_case.execute(analysis_id=analysis.id.value)
