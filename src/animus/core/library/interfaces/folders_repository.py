from typing import Protocol

from animus.core.library.domain.entities.folder import Folder
from animus.core.shared.domain.structures import Id, Integer, Text
from animus.core.shared.responses import CursorPaginationResponse


class FoldersRepository(Protocol):
    def find_by_id(self, folder_id: Id) -> Folder | None: ...

    def find_many(
        self,
        account_id: Id,
        search: Text,
        cursor: Id | None,
        limit: Integer,
    ) -> CursorPaginationResponse[Folder]: ...

    def add(self, folder: Folder) -> None: ...

    def add_many(self, folders: list[Folder]) -> None: ...

    def replace(self, folder: Folder) -> None: ...
