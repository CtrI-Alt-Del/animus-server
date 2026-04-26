from animus.core.intake.domain.entities.dtos.precedent_dto import PrecedentDto
from animus.core.intake.domain.structures.dtos.analysies_precedent_legal_features_dto import (
    AnalysiesPrecedentLegalFeaturesDto,
)
from animus.core.shared.domain.decorators import dto


@dto
class AnalysisPrecedentDto:
    analysis_id: str
    precedent: PrecedentDto
    is_chosen: bool = False
    similarity_score: float | None = None
    synthesis: str | None = None
    thesis_similarity_score: float = 0.0
    enunciation_similarity_score: float = 0.0
    total_search_hits: int = 0
    similarity_rank: int = 0
    applicability_level: int | None = None
    legal_features: AnalysiesPrecedentLegalFeaturesDto | None = None
