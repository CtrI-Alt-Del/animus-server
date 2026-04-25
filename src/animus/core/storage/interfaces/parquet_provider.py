from typing import Protocol

from animus.core.intake.domain.structures.dtos.analysis_precedent_dataset_dto import (
    AnalysisPrecedentDatasetDto,
)
from animus.core.shared.domain.structures import FilePath


class ParquetProvider(Protocol):
    def write_analysis_precedents_dataset(
        self,
        rows: list[AnalysisPrecedentDatasetDto],
        local_file_path: FilePath,
    ) -> None: ...
