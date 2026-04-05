from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.entities.dtos.petition_dto import PetitionDto
from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.intake.domain.structures.dtos.petition_summary_dto import (
    PetitionSummaryDto,
)
from animus.core.shared.domain.decorators import dto


@dto
class AnalysisReportDto:
    analysis: AnalysisDto
    petition: PetitionDto
    summary: PetitionSummaryDto
    precedents: list[AnalysisPrecedentDto]
    chosen_precedent: AnalysisPrecedentDto | None
