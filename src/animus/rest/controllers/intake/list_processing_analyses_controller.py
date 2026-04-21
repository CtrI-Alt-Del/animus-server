from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.use_cases.list_processing_analyses_use_case import (
    ListProcessingAnalysesUseCase,
)
from animus.core.shared.domain.structures.id import Id
from animus.pipes.auth_pipe import (
    AuthPipe,
)
from animus.pipes.database_pipe import DatabasePipe


class ListProcessingAnalysesController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/analyses/processing',
            status_code=200,
            response_model=list[AnalysisDto],
        )
        def _(
            account_id: Annotated[
                Id,
                Depends(AuthPipe.get_account_id_from_request),
            ],
            analisyses_repository: Annotated[
                AnalisysesRepository,
                Depends(DatabasePipe.get_analisyses_repository_from_request),
            ],
        ) -> list[AnalysisDto]:
            use_case = ListProcessingAnalysesUseCase(
                analisyses_repository=analisyses_repository,
            )

            return use_case.execute(account_id=account_id.value)
