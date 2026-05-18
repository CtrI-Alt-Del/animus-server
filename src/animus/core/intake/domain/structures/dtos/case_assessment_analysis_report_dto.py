from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.intake.domain.structures.dtos.case_summary_dto import (
    CaseSummaryDto,
)
from animus.core.intake.domain.structures.dtos.petition_draft_dto import (
    PetitionDraftDto,
)
from animus.core.shared.domain.decorators import dto


@dto
class CaseAssessmentAnalysisReportDto:
    analysis: AnalysisDto
    document: AnalysisDocumentDto
    case_summary: CaseSummaryDto
    precedents: list[AnalysisPrecedentDto]
    petition_draft: PetitionDraftDto
    chosen_precedent: AnalysisPrecedentDto | None
