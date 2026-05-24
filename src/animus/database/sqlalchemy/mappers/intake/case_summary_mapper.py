from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.dtos.case_summary_dto import CaseSummaryDto
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.models.intake.case_summary_model import CaseSummaryModel


class CaseSummaryMapper:
    @staticmethod
    def to_entity(model: CaseSummaryModel) -> CaseSummary:
        return CaseSummary.create(
            CaseSummaryDto(
                case_summary=model.case_summary,
                legal_issue=model.legal_issue,
                central_question=model.central_question,
                relevant_laws=model.relevant_laws,
                key_facts=model.key_facts,
                search_terms=model.search_terms,
                type_of_action=model.type_of_action,
                secondary_legal_issues=model.secondary_legal_issues,
                alternative_questions=model.alternative_questions,
                jurisdiction_issue=model.jurisdiction_issue,
                standing_issue=model.standing_issue,
                requested_relief=model.triggered_relief,
                procedural_issues=model.procedural_issues,
                excluded_or_accessory_topics=model.excluded_or_accessory_topics,
            )
        )

    @staticmethod
    def to_model(analysis_id: Id, case_summary: CaseSummary) -> CaseSummaryModel:
        return CaseSummaryModel(
            analysis_id=analysis_id.value,
            case_summary=case_summary.case_summary.value,
            legal_issue=case_summary.legal_issue.value,
            central_question=case_summary.central_question.value,
            relevant_laws=[item.value for item in case_summary.relevant_laws],
            key_facts=[item.value for item in case_summary.key_facts],
            search_terms=[item.value for item in case_summary.search_terms],
            type_of_action=(
                case_summary.type_of_action.value
                if case_summary.type_of_action is not None
                else None
            ),
            secondary_legal_issues=[
                item.value for item in case_summary.secondary_legal_issues
            ],
            alternative_questions=[
                item.value for item in case_summary.alternative_questions
            ],
            jurisdiction_issue=(
                case_summary.jurisdiction_issue.value
                if case_summary.jurisdiction_issue is not None
                else None
            ),
            standing_issue=(
                case_summary.standing_issue.value
                if case_summary.standing_issue is not None
                else None
            ),
            requested_relief=[item.value for item in case_summary.triggered_relief],
            procedural_issues=[item.value for item in case_summary.procedural_issues],
            excluded_or_accessory_topics=[
                item.value for item in case_summary.excluded_or_accessory_topics
            ],
        )
