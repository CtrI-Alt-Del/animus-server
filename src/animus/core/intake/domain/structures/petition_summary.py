from animus.core.intake.domain.structures.dtos.petition_summary_dto import (
    PetitionSummaryDto,
)
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.structures import Text


@structure
class PetitionSummary(Structure):
    case_summary: Text
    legal_issue: Text
    central_question: Text
    relevant_laws: list[Text]
    key_facts: list[Text]
    search_terms: list[Text]

    @classmethod
    def create(cls, dto: PetitionSummaryDto) -> 'PetitionSummary':
        return cls(
            case_summary=Text.create(dto.case_summary),
            legal_issue=Text.create(dto.legal_issue),
            central_question=Text.create(dto.central_question),
            relevant_laws=[Text.create(item) for item in dto.relevant_laws],
            key_facts=[Text.create(item) for item in dto.key_facts],
            search_terms=[Text.create(item) for item in dto.search_terms],
        )

    @property
    def dto(self) -> PetitionSummaryDto:
        return PetitionSummaryDto(
            case_summary=self.case_summary.value,
            legal_issue=self.legal_issue.value,
            central_question=self.central_question.value,
            relevant_laws=[item.value for item in self.relevant_laws],
            key_facts=[item.value for item in self.key_facts],
            search_terms=[item.value for item in self.search_terms],
        )
