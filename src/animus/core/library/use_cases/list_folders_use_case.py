from animus.core.library.domain.entities.dtos.folder_dto import FolderDto
from animus.core.library.interfaces import FoldersRepository
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id, Integer, Text
from animus.core.shared.responses import CursorPaginationResponse


class ListFoldersUseCase:
    def __init__(self, folders_repository: FoldersRepository) -> None:
        self._folders_repository = folders_repository

    def execute(
        self,
        account_id: str,
        search: str,
        cursor: str | None,
        limit: int,
    ) -> CursorPaginationResponse[FolderDto]:
        if limit < 1:
            raise ValidationError(
                f'Valor deve ser maior ou igual a 1, recebido: {limit}'
            )

        folders = self._folders_repository.find_many(
            account_id=Id.create(account_id),
            search=Text.create(search),
            cursor=Id.create(cursor) if cursor is not None else None,
            limit=Integer.create(limit),
        )

        return folders.mapItems(lambda folder: folder.dto)
