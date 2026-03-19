from animus.core.intake.domain.entities.dtos.folder_dto import FolderDto
from animus.core.shared.domain.abstracts import Entity
from animus.core.shared.domain.decorators import entity
from animus.core.shared.domain.structures import Id, Logical, Name


@entity
class Folder(Entity):
    name: Name
    account_id: Id
    is_archived: Logical

    @classmethod
    def create(cls, dto: FolderDto) -> 'Folder':
        return cls(
            id=Id.create(dto.id),
            name=Name.create(dto.name),
            account_id=Id.create(dto.account_id),
            is_archived=Logical.create(dto.is_archived),
        )

    @property
    def dto(self) -> FolderDto:
        return FolderDto(
            id=self.id.value,
            name=self.name.value,
            account_id=self.account_id.value,
            is_archived=self.is_archived.value,
        )
