from animus.core.intake.domain.entities.dtos.petition_document_dto import (
    PetitionDocumentDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import FilePath, Text


@structure
class PetitionDocument(Structure):
    file_path: FilePath
    name: Text

    @classmethod
    def create(cls, dto: PetitionDocumentDto) -> 'PetitionDocument':
        file_path = (
            dto.file_path
            if isinstance(dto.file_path, FilePath)
            else FilePath.create(dto.file_path)
        )

        return cls(
            file_path=file_path,
            name=Text.create(dto.name),
        )

    @property
    def dto(self) -> PetitionDocumentDto:
        return PetitionDocumentDto(
            file_path=self.file_path.value,
            name=self.name.value,
        )
