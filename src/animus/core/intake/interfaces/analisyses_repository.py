from typing import Protocol

from animus.core.intake.domain.entities import Analysis
from animus.core.shared.domain.structures import Id, Integer, Text
from animus.core.shared.responses import PaginationResponse


class AnalisysesRepository(Protocol):
    def find_by_id(self, account_id: Id) -> Analysis: ...

    def find_many(
        self,
        search: Text,
        cursor: Id | None,
        limit: Integer,
    ) -> PaginationResponse[Analysis]: ...

    def add(self, analysis: Analysis) -> None: ...

    def add_many(self, analyses: list[Analysis]) -> None: ...

    def replace(self, analysis: Analysis) -> None: ...
