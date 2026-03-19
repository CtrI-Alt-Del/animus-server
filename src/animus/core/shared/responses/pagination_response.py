from animus.core.shared.domain.decorators.response import response
from animus.core.shared.domain.structures import Id


@response
class PaginationResponse[Item]:
    items: list[Item]
    next_cursor: Id | None = None
