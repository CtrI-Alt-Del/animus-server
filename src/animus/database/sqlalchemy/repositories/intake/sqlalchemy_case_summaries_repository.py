from sqlalchemy.orm import Session

from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.interfaces.case_summaries_repository import (
    CaseSummariesRepository,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.mappers.intake.case_summary_mapper import (
    CaseSummaryMapper,
)
from animus.database.sqlalchemy.models.intake.case_summary_model import CaseSummaryModel


class SqlalchemyCaseSummariesRepository(CaseSummariesRepository):
    def __init__(self, sqlalchemy: Session) -> None:
        self._sqlalchemy = sqlalchemy

    def find_by_analysis_id(self, analysis_id: Id) -> CaseSummary | None:
        model = self._sqlalchemy.get(CaseSummaryModel, analysis_id.value)
        if model is None:
            return None

        return CaseSummaryMapper.to_entity(model)

    def add(self, analysis_id: Id, case_summary: CaseSummary) -> None:
        self._sqlalchemy.add(
            CaseSummaryMapper.to_model(
                analysis_id=analysis_id,
                case_summary=case_summary,
            )
        )

    def replace(self, analysis_id: Id, case_summary: CaseSummary) -> None:
        model = self._sqlalchemy.get(CaseSummaryModel, analysis_id.value)
        if model is None:
            self.add(analysis_id=analysis_id, case_summary=case_summary)
            return

        model.case_summary = case_summary.case_summary.value
        model.legal_issue = case_summary.legal_issue.value
        model.central_question = case_summary.central_question.value
        model.relevant_laws = [item.value for item in case_summary.relevant_laws]
        model.key_facts = [item.value for item in case_summary.key_facts]
        model.search_terms = [item.value for item in case_summary.search_terms]
        model.type_of_action = (
            case_summary.type_of_action.value
            if case_summary.type_of_action is not None
            else None
        )
        model.secondary_legal_issues = [
            item.value for item in case_summary.secondary_legal_issues
        ]
        model.alternative_questions = [
            item.value for item in case_summary.alternative_questions
        ]
        model.jurisdiction_issue = (
            case_summary.jurisdiction_issue.value
            if case_summary.jurisdiction_issue is not None
            else None
        )
        model.standing_issue = (
            case_summary.standing_issue.value
            if case_summary.standing_issue is not None
            else None
        )
        model.requested_relief = [item.value for item in case_summary.requested_relief]
        model.procedural_issues = [
            item.value for item in case_summary.procedural_issues
        ]
        model.excluded_or_accessory_topics = [
            item.value for item in case_summary.excluded_or_accessory_topics
        ]

    def remove_by_analysis_id(self, analysis_id: Id) -> None:
        model = self._sqlalchemy.get(CaseSummaryModel, analysis_id.value)
        if model is None:
            return

        self._sqlalchemy.delete(model)
