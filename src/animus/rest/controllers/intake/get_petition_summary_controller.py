from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.entities import Petition
from animus.core.intake.domain.structures.dtos.petition_summary_dto import (
    PetitionSummaryDto,
)
from animus.core.intake.interfaces import PetitionSummariesRepository
from animus.core.intake.use_cases import GetPetitionSummaryUseCase
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe
from animus.validation.shared import IdSchema


class GetPetitionSummaryController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/petitions/{petition_id}/summary',
            status_code=200,
            response_model=PetitionSummaryDto,
        )
        def _(
            petition_id: IdSchema,
            _petition: Annotated[
                Petition,
                Depends(IntakePipe.verify_petition_by_account),
            ],
            petition_summaries_repository: Annotated[
                PetitionSummariesRepository,
                Depends(DatabasePipe.get_petition_summaries_repository_from_request),
            ],
        ) -> PetitionSummaryDto:
            use_case = GetPetitionSummaryUseCase(
                petition_summaries_repository=petition_summaries_repository,
            )

            return use_case.execute(petition_id=petition_id)
