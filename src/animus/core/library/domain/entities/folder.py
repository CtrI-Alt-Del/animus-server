from animus.core.library.domain.entities.dtos.folder_dto import FolderDto
from animus.core.shared.domain.abstracts import Entity
from animus.core.shared.domain.decorators import entity
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id, Integer, Logical, Name


@entity
class Folder(Entity):
    name: Name
    account_id: Id
    analysis_count: Integer
    is_archived: Logical

    @classmethod
    def create(cls, dto: FolderDto) -> 'Folder':
        cls._validate_name_length(dto.name)

        return cls(
            id=Id.create(dto.id),
            name=Name.create(dto.name),
            analysis_count=Integer.create(dto.analysis_count),
            account_id=Id.create(dto.account_id),
            is_archived=Logical.create(dto.is_archived),
        )

    @property
    def dto(self) -> FolderDto:
        return FolderDto(
            id=self.id.value,
            name=self.name.value,
            analysis_count=self.analysis_count.value,
            account_id=self.account_id.value,
            is_archived=self.is_archived.value,
        )

    def rename(self, name: str) -> None:
        self._validate_name_length(name)
        self.name = Name.create(name)

    def archive(self) -> None:
        self.is_archived = Logical.create_true()

    @staticmethod
    def _validate_name_length(name: str) -> None:
        if len(name.strip()) > 50:
            raise ValidationError('Nome da pasta deve ter no maximo 50 caracteres')
