from animus.core.intake.domain.entities.analysis_type import AnalysisType
from animus.core.intake.domain.entities.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.entities.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.intake.domain.structures.dtos.analysis_precedents_search_filters_dto import (
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.core.shared.domain.decorators import dto


@dto
class AnalysisDto:
    name: str
    account_id: str
    status: str | CaseAssessmentAnalysisStatus | SecondInstanceAnalysisStatus
    created_at: str
    type: AnalysisType = AnalysisType.FIRST_INSTANCE
    folder_id: str | None = None
    is_archived: bool = False
    precedents_search_filters: AnalysisPrecedentsSearchFiltersDto | None = None
    id: str | None = None
