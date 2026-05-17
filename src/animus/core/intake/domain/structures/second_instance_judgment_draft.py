from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Id, Text


@structure
class SecondInstanceJudgmentDraft(Structure):
    analysis_id: Id
    report: Text
    merit_analysis: Text
    precedent_adherence_analysis: Text
    ruling: list[Text]
    preliminary_issues: Text | None = None
    no_applicable_precedent_notice: Text | None = None

    @classmethod
    def create(
        cls, dto: SecondInstanceJudgmentDraftDto
    ) -> 'SecondInstanceJudgmentDraft':
        return cls(
            analysis_id=Id.create(dto.analysis_id),
            report=Text.create(dto.report),
            merit_analysis=Text.create(dto.merit_analysis),
            precedent_adherence_analysis=Text.create(dto.precedent_adherence_analysis),
            ruling=[Text.create(item) for item in dto.ruling],
            preliminary_issues=(
                Text.create(dto.preliminary_issues)
                if dto.preliminary_issues is not None
                else None
            ),
            no_applicable_precedent_notice=(
                Text.create(dto.no_applicable_precedent_notice)
                if dto.no_applicable_precedent_notice is not None
                else None
            ),
        )

    @property
    def dto(self) -> SecondInstanceJudgmentDraftDto:
        return SecondInstanceJudgmentDraftDto(
            analysis_id=self.analysis_id.value,
            report=self.report.value,
            merit_analysis=self.merit_analysis.value,
            precedent_adherence_analysis=self.precedent_adherence_analysis.value,
            ruling=[item.value for item in self.ruling],
            preliminary_issues=(
                self.preliminary_issues.value
                if self.preliminary_issues is not None
                else None
            ),
            no_applicable_precedent_notice=(
                self.no_applicable_precedent_notice.value
                if self.no_applicable_precedent_notice is not None
                else None
            ),
        )
