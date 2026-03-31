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
        )
