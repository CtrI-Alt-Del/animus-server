from typing import Protocol

from animus.core.intake.domain.structures.dtos.analysis_precedent_dataset_dto import (
    AnalysisPrecedentDatasetDto,
)
from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)


class ClassifyAnalysisPrecedentsApplicabilityWorkflow(Protocol):
    def run(
        self,
        analysis_id: str,
        analysis_precedents: list[AnalysisPrecedentDto],
    ) -> list[AnalysisPrecedentDatasetDto]: ...
