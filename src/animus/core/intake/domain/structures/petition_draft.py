from animus.core.intake.domain.structures.dtos.petition_draft_dto import (
    PetitionDraftDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Id, Text


@structure
class PetitionDraft(Structure):
    analysis_id: Id
    content: Text

    @classmethod
    def create(cls, dto: PetitionDraftDto) -> 'PetitionDraft':
        return cls(
            analysis_id=Id.create(dto.analysis_id),
            content=Text.create(dto.content),
        )

    @property
    def dto(self) -> PetitionDraftDto:
        return PetitionDraftDto(
            analysis_id=self.analysis_id.value,
            content=self.content.value,
        )
