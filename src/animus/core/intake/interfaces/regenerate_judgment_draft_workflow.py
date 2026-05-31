from typing import Protocol

from animus.core.intake.domain.structures.analysis_precedent import AnalysisPrecedent
from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)
from animus.core.intake.domain.structures.second_instance_judgment_draft import (
    SecondInstanceJudgmentDraft,
)


class RegenerateSecondInstanceJudgmentDraftWorkflow(Protocol):
    def run(
        self,
        analysis_id: str,
        current_draft: SecondInstanceJudgmentDraft,
        case_summary: CaseSummary,
        precedents: list[AnalysisPrecedent],
        comments: str,
    ) -> SecondInstanceJudgmentDraftDto: ...
