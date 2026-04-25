from animus.core.intake.domain.structures.petition_summary import PetitionSummary
from animus.core.intake.domain.structures.dtos.petition_summary_dto import (
    PetitionSummaryDto,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.models.intake.petition_summary_model import (
    PetitionSummaryModel,
)


class PetitionSummaryMapper:
    @staticmethod
    def to_entity(model: PetitionSummaryModel) -> PetitionSummary:
        return PetitionSummary.create(
            PetitionSummaryDto(
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
                requested_relief=model.requested_relief,
                procedural_issues=model.procedural_issues,
                excluded_or_accessory_topics=model.excluded_or_accessory_topics,
            )
        )

    @staticmethod
    def to_model(
        petition_id: Id,
        petition_summary: PetitionSummary,
    ) -> PetitionSummaryModel:
        return PetitionSummaryModel(
            petition_id=petition_id.value,
            case_summary=petition_summary.case_summary.value,
            legal_issue=petition_summary.legal_issue.value,
            central_question=petition_summary.central_question.value,
            relevant_laws=[item.value for item in petition_summary.relevant_laws],
            key_facts=[item.value for item in petition_summary.key_facts],
            search_terms=[item.value for item in petition_summary.search_terms],
            type_of_action=(
                petition_summary.type_of_action.value
                if petition_summary.type_of_action is not None
                else None
            ),
            secondary_legal_issues=[
                item.value for item in petition_summary.secondary_legal_issues
            ],
            alternative_questions=[
                item.value for item in petition_summary.alternative_questions
            ],
            jurisdiction_issue=(
                petition_summary.jurisdiction_issue.value
                if petition_summary.jurisdiction_issue is not None
                else None
            ),
            standing_issue=(
                petition_summary.standing_issue.value
                if petition_summary.standing_issue is not None
                else None
            ),
            requested_relief=[item.value for item in petition_summary.requested_relief],
            procedural_issues=[
                item.value for item in petition_summary.procedural_issues
            ],
            excluded_or_accessory_topics=[
                item.value for item in petition_summary.excluded_or_accessory_topics
            ],
        )
