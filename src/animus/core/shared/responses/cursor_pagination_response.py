from collections.abc import Callable
from typing import Annotated

from pydantic import PlainSerializer

from animus.core.shared.domain.decorators.response import response
from animus.core.shared.domain.structures import Id

SerializedCursor = Annotated[
    Id | None,
    PlainSerializer(
        lambda value: value.value if value is not None else None,
        return_type=str | None,
        when_used='json',
    ),
]


@response
class CursorPaginationResponse[Item]:
    items: list[Item]
    next_cursor: SerializedCursor = None

    def map_items[MappedItem](
        self,
        mapper: Callable[[Item], MappedItem],
    ) -> 'CursorPaginationResponse[MappedItem]':
        return CursorPaginationResponse(
            items=[mapper(item) for item in self.items],
            next_cursor=self.next_cursor,
        )

    mapItems = map_items  # noqa: N815
