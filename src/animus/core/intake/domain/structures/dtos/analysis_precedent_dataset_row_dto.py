from animus.core.intake.domain.structures.dtos.precedent_identifier_dto import (
    PrecedentIdentifierDto,
)
from animus.core.shared.domain.decorators import dto


@dto
class AnalysisPrecedentDatasetRowDto:
    analysis_id: str
    precedent_id: str
    created_at: str
    applicability_level: int
    is_from_human: bool
    thesis_similarity_score: float
    enunciation_similarity_score: float
    total_search_hits: int
    similarity_rank: int
    identifier: PrecedentIdentifierDto
    precedent_status: str
    last_updated_in_pangea_at: str
    central_issue_match: int
    structural_issue_match: int
    context_compatibility: int
    is_lateral_topic: int
    is_accessory_topic: int
