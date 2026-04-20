from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from animus.core.library.domain.entities.dtos import FolderDto
from animus.core.library.interfaces import FoldersRepository
from animus.core.library.use_cases import RenameFolderUseCase
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe
from animus.validation.shared import IdSchema


class _Body(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class RenameFolderController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.patch('/folders/{folder_id}', status_code=200, response_model=FolderDto)
        def _(
            folder_id: IdSchema,
            body: _Body,
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
            folders_repository: Annotated[
                FoldersRepository,
                Depends(DatabasePipe.get_folders_repository_from_request),
            ],
        ) -> FolderDto:
            use_case = RenameFolderUseCase(folders_repository=folders_repository)

            return use_case.execute(
                account_id=account_id.value,
                folder_id=folder_id,
                name=body.name,
            )
