from animus.core.intake.domain.structures.dtos.petition_draft_dto import (
    PetitionDraftDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Id, Text


@structure
class PetitionDraft(Structure):
    analysis_id: Id
    structured_facts: Text
    legal_grounds: Text
    central_thesis: Text
    requests: list[Text]
    precedent_citations: list[Text]

    @classmethod
    def create(cls, dto: PetitionDraftDto) -> 'PetitionDraft':
        return cls(
            analysis_id=Id.create(dto.analysis_id),
            structured_facts=Text.create(dto.structured_facts),
            legal_grounds=Text.create(dto.legal_grounds),
            central_thesis=Text.create(dto.central_thesis),
            requests=[Text.create(item) for item in dto.requests],
            precedent_citations=[Text.create(item) for item in dto.precedent_citations],
        )

    @property
    def dto(self) -> PetitionDraftDto:
        return PetitionDraftDto(
            analysis_id=self.analysis_id.value,
            structured_facts=self.structured_facts.value,
            legal_grounds=self.legal_grounds.value,
            central_thesis=self.central_thesis.value,
            requests=[item.value for item in self.requests],
            precedent_citations=[item.value for item in self.precedent_citations],
        )
