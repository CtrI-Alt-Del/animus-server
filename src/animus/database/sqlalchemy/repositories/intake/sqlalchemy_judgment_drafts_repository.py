from sqlalchemy.orm import Session

from animus.core.intake.domain.structures.judgment_draft import JudgmentDraft
from animus.core.intake.interfaces.judgment_drafts_repository import (
    JudgmentDraftsRepository,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.mappers.intake.judgment_draft_mapper import (
    JudgmentDraftMapper,
)
from animus.database.sqlalchemy.models.intake.judgment_draft_model import (
    JudgmentDraftModel,
)


class SqlalchemyJudgmentDraftsRepository(JudgmentDraftsRepository):
    def __init__(self, sqlalchemy: Session) -> None:
        self._sqlalchemy = sqlalchemy

    def find_by_analysis_id(self, analysis_id: Id) -> JudgmentDraft | None:
        model = self._sqlalchemy.get(JudgmentDraftModel, analysis_id.value)
        if model is None:
            return None

        return JudgmentDraftMapper.to_entity(model)

    def add(self, judgment_draft: JudgmentDraft) -> None:
        self._sqlalchemy.add(JudgmentDraftMapper.to_model(judgment_draft))

    def replace(self, judgment_draft: JudgmentDraft) -> None:
        model = self._sqlalchemy.get(JudgmentDraftModel, judgment_draft.analysis_id.value)
        if model is None:
            self.add(judgment_draft)
            return

        model.content = judgment_draft.content.value
