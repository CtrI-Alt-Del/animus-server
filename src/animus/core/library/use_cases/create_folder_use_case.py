from animus.core.library.domain.entities.folder import Folder
from animus.core.library.domain.entities.dtos.folder_dto import FolderDto
from animus.core.library.interfaces import FoldersRepository
from animus.core.shared.domain.structures import Id, Logical


class CreateFolderUseCase:
    def __init__(self, folders_repository: FoldersRepository) -> None:
        self._folders_repository = folders_repository

    def execute(self, account_id: str, name: str) -> FolderDto:
        folder = Folder.create(
            FolderDto(
                name=name,
                analysis_count=0,
                account_id=Id.create(account_id).value,
                is_archived=Logical.create_false().value,
            )
        )

        self._folders_repository.add(folder)

        return folder.dto
