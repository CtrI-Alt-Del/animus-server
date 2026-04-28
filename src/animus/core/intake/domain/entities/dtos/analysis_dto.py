from animus.core.intake.domain.structures.dtos.analysis_precedents_search_filters_dto import (
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.core.shared.domain.decorators import dto


@dto
class AnalysisDto:
    name: str
    account_id: str
    status: str
    created_at: str
    folder_id: str | None = None
    is_archived: bool = False
    precedents_search_filters: AnalysisPrecedentsSearchFiltersDto | None = None
    id: str | None = None
