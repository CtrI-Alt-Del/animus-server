from animus.core.shared.domain.decorators import dto


@dto
class AnalysisDto:
    name: str
    account_id: str
    status: str
    created_at: str
    folder_id: str | None = None
    is_archived: bool = False
    id: str | None = None
