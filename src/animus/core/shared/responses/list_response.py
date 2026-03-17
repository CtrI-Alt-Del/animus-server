from animus.core.shared.domain.decorators.response import response


@response
class ListResponse[Item]:
    items: list[Item]
