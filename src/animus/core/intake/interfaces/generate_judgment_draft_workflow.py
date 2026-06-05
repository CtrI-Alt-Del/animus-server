from typing import Protocol

from animus.core.intake.domain.structures.analysis_precedent import AnalysisPrecedent
from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)
from animus.core.intake.domain.structures.second_instance_decision import (
    SecondInstanceDecision,
)


class GenerateSecondInstanceJudgmentDraftWorkflow(Protocol):
    def run(
        self,
        analysis_id: str,
        case_summary: CaseSummary,
        precedents: list[AnalysisPrecedent],
        second_instance_decision: SecondInstanceDecision,
    ) -> SecondInstanceJudgmentDraftDto: ...
