from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.use_cases.move_analyses_to_folder_use_case import (
    MoveAnalysesToFolderUseCase,
)
from animus.core.library.interfaces.folders_repository import FoldersRepository
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe


class MoveAnalysesToFolderController:
    class _Body(BaseModel):
        analysis_ids: list[str] = Field(..., min_length=1)
        folder_id: str | None = None

    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.patch(
            '/analyses/folder',
            status_code=200,
            response_model=list[AnalysisDto],
        )
        def _(
            body: MoveAnalysesToFolderController._Body,
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
            analisyses_repository: Annotated[
                AnalisysesRepository,
                Depends(DatabasePipe.get_analisyses_repository_from_request),
            ],
            folders_repository: Annotated[
                FoldersRepository,
                Depends(DatabasePipe.get_folders_repository_from_request),
            ],
        ) -> list[AnalysisDto]:
            use_case = MoveAnalysesToFolderUseCase(
                analisyses_repository=analisyses_repository,
                folders_repository=folders_repository,
            )

            return use_case.execute(
                account_id=account_id.value,
                analysis_ids=body.analysis_ids,
                folder_id=body.folder_id,
            )
