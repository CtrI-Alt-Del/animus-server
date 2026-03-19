from animus.core.intake.domain.entities.dtos.petition_document_dto import (
    PetitionDocumentDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Text


@structure
class PetitionDocument(Structure):
    file_key: Text
    name: Text

    @classmethod
    def create(cls, dto: PetitionDocumentDto) -> 'PetitionDocument':
        return cls(
            file_key=Text.create(dto.file_key),
            name=Text.create(dto.name),
        )

    @property
    def dto(self) -> PetitionDocumentDto:
        return PetitionDocumentDto(
            file_key=self.file_key.value,
            name=self.name.value,
        )
