from animus.core.library.domain.errors import FolderNotFoundError
from animus.core.library.domain.entities.dtos.folder_dto import FolderDto
from animus.core.library.interfaces import FoldersRepository
from animus.core.shared.domain.errors import ForbiddenError
from animus.core.shared.domain.structures import Id


class RenameFolderUseCase:
    def __init__(self, folders_repository: FoldersRepository) -> None:
        self._folders_repository = folders_repository

    def execute(self, account_id: str, folder_id: str, name: str) -> FolderDto:
        normalized_account_id = Id.create(account_id)
        folder = self._folders_repository.find_by_id(Id.create(folder_id))

        if folder is None:
            raise FolderNotFoundError

        if folder.account_id != normalized_account_id:
            raise ForbiddenError('Pasta nao pertence a conta autenticada')

        folder.rename(name)
        self._folders_repository.replace(folder)

        return folder.dto
