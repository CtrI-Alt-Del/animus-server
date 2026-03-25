from animus.core.shared.domain.decorators.response import response


@response
class PagePaginationResponse[Item]:
    items: list[Item]
    total: int
    page: int
    page_size: int

    @property
    def has_next_page(self) -> bool:
        return self.page * self.page_size < self.total
