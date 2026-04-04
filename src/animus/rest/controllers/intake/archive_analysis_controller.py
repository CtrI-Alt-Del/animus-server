from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.use_cases.archive_analysis_use_case import (
    ArchiveAnalysisUseCase,
)
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe


class ArchiveAnalysisController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.patch(
            '/analyses/{analysis_id}/archive',
            status_code=200,
            response_model=AnalysisDto,
        )
        def _(
            analysis_id: str,
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
            analisyses_repository: Annotated[
                AnalisysesRepository,
                Depends(DatabasePipe.get_analisyses_repository_from_request),
            ],
        ) -> AnalysisDto:
            use_case = ArchiveAnalysisUseCase(
                analisyses_repository=analisyses_repository,
            )

            return use_case.execute(
                account_id=account_id.value,
                analysis_id=analysis_id,
            )
