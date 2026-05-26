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
from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)


from animus.core.shared.domain.decorators import dto


@dto
class FirstInstanceAnalysisReportDto:
    analysis: AnalysisDto
    document: AnalysisDocumentDto
    case_summary: CaseSummaryDto
    precedents: list[AnalysisPrecedentDto]
    judgment_draft: SecondInstanceJudgmentDraftDto | None = None
