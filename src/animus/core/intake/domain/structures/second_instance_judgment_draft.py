from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Id, Text


@structure
class SecondInstanceJudgmentDraft(Structure):
    analysis_id: Id
    content: Text

    @classmethod
    def create(
        cls, dto: SecondInstanceJudgmentDraftDto
    ) -> 'SecondInstanceJudgmentDraft':
        return cls(
            analysis_id=Id.create(dto.analysis_id),
            content=Text.create(dto.content),
        )

    @property
    def dto(self) -> SecondInstanceJudgmentDraftDto:
        return SecondInstanceJudgmentDraftDto(
            analysis_id=self.analysis_id.value,
            content=self.content.value,
        )
