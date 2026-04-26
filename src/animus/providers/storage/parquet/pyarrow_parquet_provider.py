import dataclasses

import pyarrow as pa
import pyarrow.parquet as pq

from animus.ai.agno.workflows.intake.agno_classify_analysis_precedents_applicability_workflow import (
    AnalysisPrecedentDatasetRowDto,
)
from animus.core.shared.domain.structures import FilePath
from animus.core.storage.interfaces import ParquetProvider


class PyarrowParquetProvider(ParquetProvider):
    def write_analysis_precedents_dataset(
        self,
        rows: list[AnalysisPrecedentDatasetRowDto],
        local_file_path: FilePath,
    ) -> None:
        pyarrow_rows = [dataclasses.asdict(row) for row in rows]
        table: object = pa.Table.from_pylist(pyarrow_rows)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        pq.write_table(table, local_file_path.value)  # pyright: ignore[reportUnknownMemberType]
