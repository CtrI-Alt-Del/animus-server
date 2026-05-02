from typing import Protocol

from animus.core.intake.domain.structures.analysis_precedent_applicability_feedback import (
    AnalysisPrecedentApplicabilityFeedback,
)
from animus.core.shared.domain.structures import Id


class AnalysisPrecedentApplicabilityFeedbacksRepository(Protocol):
    def find_by_analysis_id_and_precedent_id(
        self,
        analysis_id: Id,
        precedent_id: Id,
    ) -> AnalysisPrecedentApplicabilityFeedback | None: ...

    def add(self, feedback: AnalysisPrecedentApplicabilityFeedback) -> None: ...

    def replace(self, feedback: AnalysisPrecedentApplicabilityFeedback) -> None: ...
