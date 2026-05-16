from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)
from animus.core.intake.domain.structures.second_instance_judgment_draft import (
    SecondInstanceJudgmentDraft,
)
from animus.database.sqlalchemy.models.intake.judgment_draft_model import (
    SecondInstanceJudgmentDraftModel,
)


class SecondInstanceJudgmentDraftMapper:
    @staticmethod
    def to_entity(
        model: SecondInstanceJudgmentDraftModel,
    ) -> SecondInstanceJudgmentDraft:
        return SecondInstanceJudgmentDraft.create(
            SecondInstanceJudgmentDraftDto(
                analysis_id=model.analysis_id,
                content=model.content,
            )
        )

    @staticmethod
    def to_model(
        judgment_draft: SecondInstanceJudgmentDraft,
    ) -> SecondInstanceJudgmentDraftModel:
        return SecondInstanceJudgmentDraftModel(
            analysis_id=judgment_draft.analysis_id.value,
            content=judgment_draft.content.value,
        )
