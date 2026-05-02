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
    type_of_action: Text | None
    secondary_legal_issues: list[Text]
    alternative_questions: list[Text]
    jurisdiction_issue: Text | None
    standing_issue: Text | None
    requested_relief: list[Text]
    procedural_issues: list[Text]
    excluded_or_accessory_topics: list[Text]

    @classmethod
    def create(cls, dto: PetitionSummaryDto) -> 'PetitionSummary':
        return cls(
            case_summary=Text.create(dto.case_summary),
            legal_issue=Text.create(dto.legal_issue),
            central_question=Text.create(dto.central_question),
            relevant_laws=[Text.create(item) for item in dto.relevant_laws],
            key_facts=[Text.create(item) for item in dto.key_facts],
            search_terms=[Text.create(item) for item in dto.search_terms],
            type_of_action=(
                Text.create(dto.type_of_action)
                if dto.type_of_action is not None
                else None
            ),
            secondary_legal_issues=[
                Text.create(item) for item in dto.secondary_legal_issues
            ],
            alternative_questions=[
                Text.create(item) for item in dto.alternative_questions
            ],
            jurisdiction_issue=(
                Text.create(dto.jurisdiction_issue)
                if dto.jurisdiction_issue is not None
                else None
            ),
            standing_issue=(
                Text.create(dto.standing_issue)
                if dto.standing_issue is not None
                else None
            ),
            requested_relief=[Text.create(item) for item in dto.requested_relief],
            procedural_issues=[Text.create(item) for item in dto.procedural_issues],
            excluded_or_accessory_topics=[
                Text.create(item) for item in dto.excluded_or_accessory_topics
            ],
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
            type_of_action=(
                self.type_of_action.value if self.type_of_action is not None else None
            ),
            secondary_legal_issues=[item.value for item in self.secondary_legal_issues],
            alternative_questions=[item.value for item in self.alternative_questions],
            jurisdiction_issue=(
                self.jurisdiction_issue.value
                if self.jurisdiction_issue is not None
                else None
            ),
            standing_issue=(
                self.standing_issue.value if self.standing_issue is not None else None
            ),
            requested_relief=[item.value for item in self.requested_relief],
            procedural_issues=[item.value for item in self.procedural_issues],
            excluded_or_accessory_topics=[
                item.value for item in self.excluded_or_accessory_topics
            ],
        )
