from sqlalchemy import select
from sqlalchemy.orm import Session

from animus.core.intake.domain.structures import AnalysisPrecedentApplicabilityFeedback
from animus.core.intake.interfaces import (
    AnalysisPrecedentApplicabilityFeedbacksRepository,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.mappers.intake import (
    AnalysisPrecedentApplicabilityFeedbackMapper,
)
from animus.database.sqlalchemy.models.intake import (
    AnalysisPrecedentApplicabilityFeedbackModel,
)


class SqlalchemyAnalysisPrecedentApplicabilityFeedbacksRepository(
    AnalysisPrecedentApplicabilityFeedbacksRepository
):
    def __init__(self, sqlalchemy: Session) -> None:
        self._sqlalchemy = sqlalchemy

    def find_by_analysis_id_and_precedent_id(
        self,
        analysis_id: Id,
        precedent_id: Id,
    ) -> AnalysisPrecedentApplicabilityFeedback | None:
        model = self._sqlalchemy.scalar(
            select(AnalysisPrecedentApplicabilityFeedbackModel).where(
                AnalysisPrecedentApplicabilityFeedbackModel.analysis_id
                == analysis_id.value,
                AnalysisPrecedentApplicabilityFeedbackModel.precedent_id
                == precedent_id.value,
            )
        )
        if model is None:
            return None

        return AnalysisPrecedentApplicabilityFeedbackMapper.to_entity(model)

    def add(self, feedback: AnalysisPrecedentApplicabilityFeedback) -> None:
        self._sqlalchemy.add(
            AnalysisPrecedentApplicabilityFeedbackMapper.to_model(feedback)
        )
        self._sqlalchemy.flush()

    def replace(self, feedback: AnalysisPrecedentApplicabilityFeedback) -> None:
        model = self._sqlalchemy.scalar(
            select(AnalysisPrecedentApplicabilityFeedbackModel).where(
                AnalysisPrecedentApplicabilityFeedbackModel.analysis_id
                == feedback.analysis_id.value,
                AnalysisPrecedentApplicabilityFeedbackModel.precedent_id
                == feedback.precedent_id.value,
            )
        )
        if model is None:
            return

        model.applicability_level = feedback.applicability_level.dto
        model.is_from_human = feedback.is_from_human.value
        model.created_at = feedback.created_at.value
        self._sqlalchemy.flush()
