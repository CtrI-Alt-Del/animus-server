from animus.core.shared.domain.decorators import dto


@dto
class FolderDto:
    name: str
    account_id: str
    is_archived: bool = False
    id: str | None = None
