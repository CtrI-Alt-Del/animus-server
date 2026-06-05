from typing import Protocol

from animus.core.intake.domain.structures.case_assessment_briefing import (
    CaseAssessmentBriefing,
)
from animus.core.shared.domain.structures import Id


class CaseAssessmentBriefingsRepository(Protocol):
    def find_by_analysis_id(self, analysis_id: Id) -> CaseAssessmentBriefing | None: ...

    def add(self, briefing: CaseAssessmentBriefing) -> None: ...

    def replace(self, briefing: CaseAssessmentBriefing) -> None: ...
