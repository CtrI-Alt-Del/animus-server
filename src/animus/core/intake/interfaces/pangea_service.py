from typing import Protocol

from animus.core.intake.domain.entities.precedent import Precedent
from animus.core.shared.responses.page_pagination_response import PagePaginationResponse


class PangeaService(Protocol):
    def fetch_precedents(
        self, page: int, page_size: int
    ) -> PagePaginationResponse[Precedent]: ...
