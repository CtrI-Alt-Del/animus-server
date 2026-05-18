from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.domain.structures.dtos.case_summary_dto import (
    CaseSummaryDto,
)
from animus.core.shared.domain.decorators import dto


@dto
class AnalysisPetitionDto:
    document: AnalysisDocumentDto
    case_summary: CaseSummaryDto | None
