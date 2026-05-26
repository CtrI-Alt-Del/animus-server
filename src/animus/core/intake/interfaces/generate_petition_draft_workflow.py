from typing import Protocol

from animus.core.intake.domain.structures.analysis_precedent import AnalysisPrecedent
from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.dtos.petition_draft_dto import (
    PetitionDraftDto,
)


class GeneratePetitionDraftWorkflow(Protocol):
    def run(
        self,
        analysis_id: str,
        case_summary: CaseSummary,
        precedents: list[AnalysisPrecedent],
    ) -> PetitionDraftDto: ...
