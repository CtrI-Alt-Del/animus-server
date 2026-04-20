from animus.core.shared.domain.decorators import dto


@dto
class FolderDto:
    id: str | None = None
    name: str
    analysis_count: int
    account_id: str
    is_archived: bool = False
