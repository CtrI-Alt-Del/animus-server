from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.domain.structures.dtos.case_summary_dto import (
    CaseSummaryDto,
)
from animus.core.shared.domain.decorators import dto


@dto
class SecondInstanceAnalysisReportDto:
    analysis: AnalysisDto
    document: AnalysisDocumentDto
    case_summary: CaseSummaryDto
    precedents: list[AnalysisPrecedentDto]
    chosen_precedent: AnalysisPrecedentDto | None
