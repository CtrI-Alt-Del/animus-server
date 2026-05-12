from animus.core.intake.domain.structures.dtos.judgment_draft_dto import JudgmentDraftDto
from animus.core.intake.domain.structures.judgment_draft import JudgmentDraft
from animus.database.sqlalchemy.models.intake.judgment_draft_model import (
    JudgmentDraftModel,
)


class JudgmentDraftMapper:
    @staticmethod
    def to_entity(model: JudgmentDraftModel) -> JudgmentDraft:
        return JudgmentDraft.create(
            JudgmentDraftDto(
                analysis_id=model.analysis_id,
                content=model.content,
            )
        )

    @staticmethod
    def to_model(judgment_draft: JudgmentDraft) -> JudgmentDraftModel:
        return JudgmentDraftModel(
            analysis_id=judgment_draft.analysis_id.value,
            content=judgment_draft.content.value,
        )
