from typing import Protocol

from animus.core.intake.domain.structures.analysis_precedent import AnalysisPrecedent
from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.dtos.petition_draft_dto import (
    PetitionDraftDto,
)
from animus.core.intake.domain.structures.petition_draft import PetitionDraft


class RegeneratePetitionDraftWorkflow(Protocol):
    def run(
        self,
        analysis_id: str,
        current_draft: PetitionDraft,
        case_summary: CaseSummary,
        precedents: list[AnalysisPrecedent],
        comments: str,
    ) -> PetitionDraftDto: ...
