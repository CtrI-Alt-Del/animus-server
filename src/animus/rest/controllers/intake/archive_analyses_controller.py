from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.use_cases.archive_analyses_use_case import (
    ArchiveAnalysesUseCase,
)
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe


class ArchiveAnalysesController:
    class _Body(BaseModel):
        analysis_ids: list[str] = Field(..., min_length=1)

    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.patch(
            '/analyses/archive',
            status_code=200,
            response_model=list[AnalysisDto],
        )
        def _(
            body: ArchiveAnalysesController._Body,
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
            analisyses_repository: Annotated[
                AnalisysesRepository,
                Depends(DatabasePipe.get_analisyses_repository_from_request),
            ],
        ) -> list[AnalysisDto]:
            use_case = ArchiveAnalysesUseCase(
                analisyses_repository=analisyses_repository,
            )

            return use_case.execute(
                account_id=account_id.value,
                analysis_ids=body.analysis_ids,
            )
