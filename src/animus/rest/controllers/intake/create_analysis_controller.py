from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.use_cases.create_analysis_use_case import CreateAnalysisUseCase
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe


class _Body(BaseModel):
    folder_id: str | None = None


class CreateAnalysisController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post('/analyses', status_code=201, response_model=AnalysisDto)
        def _(
            body: _Body,
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
            analisyses_repository: Annotated[
                AnalisysesRepository,
                Depends(DatabasePipe.get_analisyses_repository_from_request),
            ],
        ) -> AnalysisDto:
            use_case = CreateAnalysisUseCase(
                analisyses_repository=analisyses_repository,
            )

            return use_case.execute(
                account_id=account_id.value,
                folder_id=body.folder_id,
            )
