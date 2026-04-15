from animus.core.shared.domain.decorators import dto


@dto
class FolderDto:
    id: str | None = None
    name: str
    account_id: str
    is_archived: bool = False
