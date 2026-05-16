from sqlalchemy.orm import Session

from animus.core.intake.domain.structures.second_instance_judgment_draft import (
    SecondInstanceJudgmentDraft,
)
from animus.core.intake.interfaces.judgment_drafts_repository import (
    SecondInstanceJudgmentDraftsRepository,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.mappers.intake.judgment_draft_mapper import (
    SecondInstanceJudgmentDraftMapper,
)
from animus.database.sqlalchemy.models.intake.judgment_draft_model import (
    SecondInstanceJudgmentDraftModel,
)


class SqlalchemySecondInstanceJudgmentDraftsRepository(
    SecondInstanceJudgmentDraftsRepository
):
    def __init__(self, sqlalchemy: Session) -> None:
        self._sqlalchemy = sqlalchemy

    def find_by_analysis_id(
        self, analysis_id: Id
    ) -> SecondInstanceJudgmentDraft | None:
        model = self._sqlalchemy.get(
            SecondInstanceJudgmentDraftModel, analysis_id.value
        )
        if model is None:
            return None

        return SecondInstanceJudgmentDraftMapper.to_entity(model)

    def add(self, judgment_draft: SecondInstanceJudgmentDraft) -> None:
        self._sqlalchemy.add(SecondInstanceJudgmentDraftMapper.to_model(judgment_draft))

    def replace(self, judgment_draft: SecondInstanceJudgmentDraft) -> None:
        model = self._sqlalchemy.get(
            SecondInstanceJudgmentDraftModel, judgment_draft.analysis_id.value
        )
        if model is None:
            self.add(judgment_draft)
            return

        model.content = judgment_draft.content.value
