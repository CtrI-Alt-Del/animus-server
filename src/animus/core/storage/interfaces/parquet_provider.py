from typing import Protocol

from animus.core.intake.domain.structures.dtos.analysis_precedent_dataset_row_dto import (
    AnalysisPrecedentDatasetRowDto,
)
from animus.core.shared.domain.structures import FilePath


class ParquetProvider(Protocol):
    def write_analysis_precedents_dataset(
        self,
        rows: list[AnalysisPrecedentDatasetRowDto],
        local_file_path: FilePath,
    ) -> None: ...
