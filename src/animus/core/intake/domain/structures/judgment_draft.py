from animus.core.intake.domain.structures.dtos.judgment_draft_dto import (
    JudgmentDraftDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Id, Text


@structure
class JudgmentDraft(Structure):
    analysis_id: Id
    content: Text

    @classmethod
    def create(cls, dto: JudgmentDraftDto) -> 'JudgmentDraft':
        return cls(
            analysis_id=Id.create(dto.analysis_id),
            content=Text.create(dto.content),
        )

    @property
    def dto(self) -> JudgmentDraftDto:
        return JudgmentDraftDto(
            analysis_id=self.analysis_id.value,
            content=self.content.value,
        )
