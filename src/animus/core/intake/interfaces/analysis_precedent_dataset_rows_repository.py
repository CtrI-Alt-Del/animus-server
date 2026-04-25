from typing import Protocol

from animus.core.intake.domain.structures.analysis_precedent_dataset_row import (
    AnalysisPrecedentDatasetRow,
)
from animus.core.shared.domain.structures import Id


class AnalysisPrecedentDatasetRowsRepository(Protocol):
    def find_by_analysis_id_and_precedent_id(
        self,
        analysis_id: Id,
        precedent_id: Id,
    ) -> AnalysisPrecedentDatasetRow | None: ...

    def add(self, dataset_row: AnalysisPrecedentDatasetRow) -> None: ...

    def replace(self, dataset_row: AnalysisPrecedentDatasetRow) -> None: ...
