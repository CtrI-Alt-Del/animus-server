from animus.core.intake.domain.structures.analysis_precedent_applicability_level import (
    AnalysisPrecedentApplicabilityLevel,
)
from animus.core.intake.domain.structures.dtos.analysis_precedent_applicability_feedback_dto import (
    AnalysisPrecedentApplicabilityFeedbackDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Datetime, Id, Logical


@structure
class AnalysisPrecedentApplicabilityFeedback(Structure):
    analysis_precedent_id: Id
    applicability_level: AnalysisPrecedentApplicabilityLevel
    is_from_human: Logical
    created_at: Datetime

    @classmethod
    def create(
        cls,
        dto: AnalysisPrecedentApplicabilityFeedbackDto,
    ) -> 'AnalysisPrecedentApplicabilityFeedback':
        return cls(
            analysis_precedent_id=Id.create(dto.analysis_precedent_id),
            applicability_level=AnalysisPrecedentApplicabilityLevel.create(
                dto.applicability_level
            ),
            is_from_human=Logical.create(dto.is_from_human),
            created_at=Datetime.create(dto.created_at),
        )

    @property
    def dto(self) -> AnalysisPrecedentApplicabilityFeedbackDto:
        return AnalysisPrecedentApplicabilityFeedbackDto(
            analysis_precedent_id=self.analysis_precedent_id.value,
            applicability_level=self.applicability_level.value,
            is_from_human=self.is_from_human.value,
            created_at=self.created_at.value.isoformat(),
        )
