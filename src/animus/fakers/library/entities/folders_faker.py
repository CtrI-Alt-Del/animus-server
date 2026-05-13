from faker import Faker

from animus.core.library.domain.entities.dtos.folder_dto import FolderDto
from animus.core.library.domain.entities.folder import Folder

_faker = Faker()


class FoldersFaker:
    @staticmethod
    def fake(
        folder_id: str | None = None,
        name: str | None = None,
        account_id: str | None = None,
        analysis_count: int | None = None,
        is_archived: bool | None = None,
    ) -> Folder:
        generated_name = name or _faker.word()
        while len(generated_name) < 2:
            generated_name = _faker.word()

        dto = FolderDto(
            id=folder_id or _faker.ulid(),
            name=generated_name,
            account_id=account_id or _faker.ulid(),
            analysis_count=analysis_count if analysis_count is not None else 0,
            is_archived=is_archived if is_archived is not None else False,
        )

        return Folder.create(dto)
