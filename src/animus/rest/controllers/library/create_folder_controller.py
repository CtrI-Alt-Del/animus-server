from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from animus.core.library.domain.entities.dtos import FolderDto
from animus.core.library.interfaces import FoldersRepository
from animus.core.library.use_cases import CreateFolderUseCase
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe


class _Body(BaseModel):
    name: str = Field(min_length=2, max_length=50)


class CreateFolderController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post('/folders', status_code=201, response_model=FolderDto)
        def _(
            body: _Body,
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
            folders_repository: Annotated[
                FoldersRepository,
                Depends(DatabasePipe.get_folders_repository_from_request),
            ],
        ) -> FolderDto:
            use_case = CreateFolderUseCase(folders_repository=folders_repository)

            return use_case.execute(account_id=account_id.value, name=body.name)
