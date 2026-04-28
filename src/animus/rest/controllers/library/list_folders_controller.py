from typing import Annotated

from fastapi import APIRouter, Depends, Query

from animus.core.library.domain.entities.dtos import FolderDto
from animus.core.library.interfaces import FoldersRepository
from animus.core.library.use_cases import ListFoldersUseCase
from animus.core.shared.domain.structures import Id
from animus.core.shared.responses import CursorPaginationResponse
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe


class ListFoldersController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/folders',
            status_code=200,
            response_model=CursorPaginationResponse[FolderDto],
        )
        def _(
            limit: Annotated[int, Query(ge=1)],
            search: str = '',
            cursor: str | None = None,
            account_id: Id = Depends(AuthPipe.get_account_id_from_request),
            folders_repository: FoldersRepository = Depends(
                DatabasePipe.get_folders_repository_from_request
            ),
        ) -> CursorPaginationResponse[FolderDto]:
            use_case = ListFoldersUseCase(folders_repository=folders_repository)

            return use_case.execute(
                account_id=account_id.value,
                search=search,
                cursor=cursor,
                limit=limit,
            )
