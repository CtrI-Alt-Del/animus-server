from pydantic import BaseModel


class CursorPaginationResponseSchema[ItemT](BaseModel):
    items: list[ItemT]
    next_cursor: str | None
