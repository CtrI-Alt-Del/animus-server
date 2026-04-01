from typing import Protocol

from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.shared.domain.structures import Id, Integer, Logical, Text
from animus.core.shared.responses import CursorPaginationResponse


class AnalisysesRepository(Protocol):
    def find_by_id(self, analysis_id: Id) -> Analysis | None: ...

    def find_many(
        self,
        account_id: Id,
        search: Text,
        cursor: Id | None,
        limit: Integer,
        is_archived: Logical,
    ) -> CursorPaginationResponse[Analysis]: ...

    def find_next_generated_name_number(self, account_id: Id) -> Integer: ...

    def add(self, analysis: Analysis) -> None: ...

    def add_many(self, analyses: list[Analysis]) -> None: ...

    def replace(self, analysis: Analysis) -> None: ...
