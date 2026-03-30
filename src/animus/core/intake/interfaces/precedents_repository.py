from typing import Protocol

from animus.core.intake.domain.entities import Precedent
from animus.core.intake.domain.structures.precedent_identifier import (
    PrecedentIdentifier,
)
from animus.core.shared.responses import ListResponse
from animus.core.shared.responses.page_pagination_response import PagePaginationResponse


class PrecedentsRepository(Protocol):
    def find_by_identifier(
        self, identifier: PrecedentIdentifier
    ) -> Precedent | None: ...

    def find_many_by_identifiers(
        self,
        identifiers: list[PrecedentIdentifier],
    ) -> ListResponse[Precedent]: ...

    def add_many(self, precedents: list[Precedent]) -> None: ...

    def find_all_identifiers(self) -> set[PrecedentIdentifier]: ...

    def find_page(
        self, page: int, page_size: int
    ) -> PagePaginationResponse[Precedent]: ...
