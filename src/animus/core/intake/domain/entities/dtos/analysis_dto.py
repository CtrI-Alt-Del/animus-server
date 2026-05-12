from animus.core.intake.domain.entities.analysis_type import AnalysisType
from animus.core.intake.domain.entities.judge_analysis_status import JudgeAnalysisStatus
from animus.core.intake.domain.entities.lawyer_analysis_status import LawyerAnalysisStatus
from animus.core.intake.domain.structures.dtos.analysis_precedents_search_filters_dto import (
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.core.shared.domain.decorators import dto


@dto
class AnalysisDto:
    name: str
    account_id: str
    status: str | LawyerAnalysisStatus | JudgeAnalysisStatus
    created_at: str
    type: AnalysisType = AnalysisType.LAWYER
    folder_id: str | None = None
    is_archived: bool = False
    precedents_search_filters: AnalysisPrecedentsSearchFiltersDto | None = None
    id: str | None = None
