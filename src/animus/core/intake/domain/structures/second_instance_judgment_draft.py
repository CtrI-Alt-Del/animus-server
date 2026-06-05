from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError
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
        report = cls._normalize_required_text(dto.report, 'Relatorio obrigatorio')
        merit_analysis = cls._normalize_required_text(
            dto.merit_analysis,
            'Analise de merito obrigatoria',
        )
        precedent_adherence_analysis = cls._normalize_required_text(
            dto.precedent_adherence_analysis,
            'Analise de aderencia a precedentes obrigatoria',
        )
        ruling = cls._normalize_ruling(dto.ruling)

        return cls(
            analysis_id=Id.create(dto.analysis_id),
            report=Text.create(report),
            merit_analysis=Text.create(merit_analysis),
            precedent_adherence_analysis=Text.create(precedent_adherence_analysis),
            ruling=[Text.create(item) for item in ruling],
            preliminary_issues=(
                Text.create(dto.preliminary_issues.strip())
                if dto.preliminary_issues is not None
                else None
            ),
            no_applicable_precedent_notice=(
                Text.create(dto.no_applicable_precedent_notice.strip())
                if dto.no_applicable_precedent_notice is not None
                else None
            ),
        )

    @staticmethod
    def _normalize_required_text(value: str, error_message: str) -> str:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValidationError(error_message)

        return normalized_value

    @staticmethod
    def _normalize_ruling(ruling: list[str]) -> list[str]:
        if not ruling:
            raise ValidationError('Dispositivo obrigatorio')

        normalized_ruling = [item.strip() for item in ruling]
        if any(not item for item in normalized_ruling):
            raise ValidationError('Dispositivo nao pode conter itens vazios')

        return normalized_ruling

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
