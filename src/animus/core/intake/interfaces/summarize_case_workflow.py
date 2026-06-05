from typing import Protocol

from animus.core.intake.domain.structures.dtos.case_assessment_briefing_dto import (
    CaseAssessmentBriefingDto,
)
from animus.core.intake.domain.structures.dtos.case_summary_dto import CaseSummaryDto
from animus.core.shared.domain.structures import Text


class SummarizeFirstInstanceCaseWorkflow(Protocol):
    def run(self, analysis_id: str, document_content: Text) -> CaseSummaryDto: ...


class SummarizeCaseAssessmentCaseWorkflow(Protocol):
    def run(
        self,
        analysis_id: str,
        briefing: CaseAssessmentBriefingDto,
        document_contents: list[Text],
    ) -> CaseSummaryDto: ...
