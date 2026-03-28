from animus.core.intake.domain.entities.dtos.precedent_dto import PrecedentDto
from animus.core.shared.domain.decorators import dto


@dto
class AnalysisPrecedentDto:
    analysis_id: str
    precedent: PrecedentDto
    is_chosen: bool = False
    applicability_percentage: float | None = None
    synthesis: str | None = None
