from animus.core.shared.domain.decorators import dto


@dto
class FolderDto:
    name: str
    analysis_count: int = 0
    account_id: str
    is_archived: bool = False
    id: str | None = None
