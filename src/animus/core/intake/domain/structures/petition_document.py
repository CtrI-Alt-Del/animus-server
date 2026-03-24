from animus.core.intake.domain.entities.dtos.petition_document_dto import (
    PetitionDocumentDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Text


@structure
class PetitionDocument(Structure):
    file_path: Text
    name: Text

    @classmethod
    def create(cls, dto: PetitionDocumentDto) -> 'PetitionDocument':
        return cls(
            file_path=Text.create(dto.file_path),
            name=Text.create(dto.name),
        )

    @property
    def dto(self) -> PetitionDocumentDto:
        return PetitionDocumentDto(
            file_path=self.file_path.value,
            name=self.name.value,
        )
