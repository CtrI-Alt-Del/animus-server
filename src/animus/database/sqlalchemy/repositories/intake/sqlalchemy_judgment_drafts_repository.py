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

        model.report = judgment_draft.report.value
        model.merit_analysis = judgment_draft.merit_analysis.value
        model.precedent_adherence_analysis = (
            judgment_draft.precedent_adherence_analysis.value
        )
        model.ruling = [item.value for item in judgment_draft.ruling]
        model.preliminary_issues = (
            judgment_draft.preliminary_issues.value
            if judgment_draft.preliminary_issues is not None
            else None
        )
        model.no_applicable_precedent_notice = (
            judgment_draft.no_applicable_precedent_notice.value
            if judgment_draft.no_applicable_precedent_notice is not None
            else None
        )
