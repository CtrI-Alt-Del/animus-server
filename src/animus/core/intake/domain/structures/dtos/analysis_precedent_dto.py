from animus.core.intake.domain.entities.dtos.precedent_dto import PrecedentDto
from animus.core.shared.domain.decorators import dto


@dto
class AnalysisPrecedentDto:
    analysis_id: str
    precedent: PrecedentDto
    applicability_percentage: float | None = None
    is_chosen: bool = False
