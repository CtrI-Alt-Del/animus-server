from animus.core.intake.domain.structures import AnalysisPrecedentApplicabilityFeedback
from animus.core.intake.domain.structures.dtos.analysis_precedent_applicability_feedback_dto import (
    AnalysisPrecedentApplicabilityFeedbackDto,
)
from animus.core.intake.interfaces import (
    AnalysisPrecedentApplicabilityFeedbacksRepository,
)
from animus.core.shared.domain.structures import Datetime, Id


class CreateAnalysisPrecedentApplicabilityFeedbackUseCase:
    def __init__(
        self,
        feedbacks_repository: AnalysisPrecedentApplicabilityFeedbacksRepository,
    ) -> None:
        self._feedbacks_repository = feedbacks_repository

    def execute(
        self,
        analysis_id: str,
        precedent_id: str,
        applicability_level: int,
    ) -> AnalysisPrecedentApplicabilityFeedbackDto:
        analysis_id_entity = Id.create(analysis_id)
        precedent_id_entity = Id.create(precedent_id)

        feedback = AnalysisPrecedentApplicabilityFeedback.create(
            AnalysisPrecedentApplicabilityFeedbackDto(
                analysis_id=analysis_id_entity.value,
                precedent_id=precedent_id_entity.value,
                applicability_level=applicability_level,
                is_from_human=False,
                created_at=Datetime.create_at_now().value.isoformat(),
            )
        )

        existing_feedback = (
            self._feedbacks_repository.find_by_analysis_id_and_precedent_id(
                analysis_id=analysis_id_entity,
                precedent_id=precedent_id_entity,
            )
        )

        if existing_feedback is None:
            self._feedbacks_repository.add(feedback)
        else:
            self._feedbacks_repository.replace(feedback)

        return feedback.dto
