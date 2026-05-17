from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)
from animus.core.intake.domain.structures.second_instance_judgment_draft import (
    SecondInstanceJudgmentDraft,
)
from animus.database.sqlalchemy.models.intake.judgment_draft_model import (
    SecondInstanceJudgmentDraftModel,
)


class SecondInstanceJudgmentDraftMapper:
    @staticmethod
    def to_entity(
        model: SecondInstanceJudgmentDraftModel,
    ) -> SecondInstanceJudgmentDraft:
        return SecondInstanceJudgmentDraft.create(
            SecondInstanceJudgmentDraftDto(
                analysis_id=model.analysis_id,
                report=model.report,
                merit_analysis=model.merit_analysis,
                precedent_adherence_analysis=model.precedent_adherence_analysis,
                ruling=model.ruling,
                preliminary_issues=model.preliminary_issues,
                no_applicable_precedent_notice=model.no_applicable_precedent_notice,
            )
        )

    @staticmethod
    def to_model(
        judgment_draft: SecondInstanceJudgmentDraft,
    ) -> SecondInstanceJudgmentDraftModel:
        return SecondInstanceJudgmentDraftModel(
            analysis_id=judgment_draft.analysis_id.value,
            report=judgment_draft.report.value,
            merit_analysis=judgment_draft.merit_analysis.value,
            precedent_adherence_analysis=judgment_draft.precedent_adherence_analysis.value,
            ruling=[item.value for item in judgment_draft.ruling],
            preliminary_issues=(
                judgment_draft.preliminary_issues.value
                if judgment_draft.preliminary_issues is not None
                else None
            ),
            no_applicable_precedent_notice=(
                judgment_draft.no_applicable_precedent_notice.value
                if judgment_draft.no_applicable_precedent_notice is not None
                else None
            ),
        )
