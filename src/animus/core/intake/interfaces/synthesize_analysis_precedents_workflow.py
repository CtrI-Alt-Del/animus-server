from typing import Protocol

from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.intake.domain.structures.dtos.analysis_precedents_search_filters_dto import (
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.core.intake.domain.structures.second_instance_decision import (
    SecondInstanceDecision,
)


class SynthesizeAnalysisPrecedentsWorkflow(Protocol):
    def run(
        self,
        analysis_id: str,
        filters_dto: AnalysisPrecedentsSearchFiltersDto,
        analysis_precedents: list[AnalysisPrecedentDto],
        second_instance_decision: SecondInstanceDecision | None = None,
    ) -> None: ...
