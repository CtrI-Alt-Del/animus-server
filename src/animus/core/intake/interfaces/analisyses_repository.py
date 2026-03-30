from typing import Protocol

from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.shared.domain.structures import Id, Integer, Text
from animus.core.shared.responses import CursorPaginationResponse


class AnalisysesRepository(Protocol):
    def find_by_id(self, analysis_id: Id) -> Analysis | None: ...

    def find_many(
        self,
        search: Text,
        cursor: Id | None,
        limit: Integer,
    ) -> CursorPaginationResponse[Analysis]: ...

    def add(self, analysis: Analysis) -> None: ...

    def add_many(self, analyses: list[Analysis]) -> None: ...

    def replace(self, analysis: Analysis) -> None: ...
