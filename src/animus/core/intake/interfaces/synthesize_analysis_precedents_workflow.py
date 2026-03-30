from typing import Protocol

from animus.core.intake.domain.structures import AnalysisPrecedent
from animus.core.intake.domain.structures.petition_summary import PetitionSummary
from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.shared.responses import ListResponse


class SynthesizeAnalysisPrecedentsWorkflow(Protocol):
    def run(
        self,
        petition_summary: PetitionSummary,
        analysis_precedents: list[AnalysisPrecedentDto],
    ) -> ListResponse[AnalysisPrecedent]: ...
