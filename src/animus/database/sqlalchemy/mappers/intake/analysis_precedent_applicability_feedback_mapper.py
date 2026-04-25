from animus.core.intake.domain.structures import AnalysisPrecedentApplicabilityFeedback
from animus.core.intake.domain.structures.dtos.analysis_precedent_applicability_feedback_dto import (
    AnalysisPrecedentApplicabilityFeedbackDto,
)
from animus.database.sqlalchemy.models.intake.analysis_precedent_applicability_feedback_model import (
    AnalysisPrecedentApplicabilityFeedbackModel,
)


class AnalysisPrecedentApplicabilityFeedbackMapper:
    @staticmethod
    def to_entity(
        model: AnalysisPrecedentApplicabilityFeedbackModel,
    ) -> AnalysisPrecedentApplicabilityFeedback:
        return AnalysisPrecedentApplicabilityFeedback.create(
            AnalysisPrecedentApplicabilityFeedbackDto(
                analysis_id=model.analysis_id,
                precedent_id=model.precedent_id,
                applicability_level=model.applicability_level,
                is_from_human=model.is_from_human,
                created_at=model.created_at.isoformat(),
            )
        )

    @staticmethod
    def to_model(
        feedback: AnalysisPrecedentApplicabilityFeedback,
    ) -> AnalysisPrecedentApplicabilityFeedbackModel:
        return AnalysisPrecedentApplicabilityFeedbackModel(
            analysis_id=feedback.analysis_id.value,
            precedent_id=feedback.precedent_id.value,
            applicability_level=feedback.applicability_level.dto,
            is_from_human=feedback.is_from_human.value,
            created_at=feedback.created_at.value,
        )
