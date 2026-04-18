from animus.core.intake.domain.entities.precedent import Precedent
from animus.core.intake.domain.structures.analysis_precedent_applicability_level import (
    AnalysisPrecedentApplicabilityLevel,
)
from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import (
    Decimal,
    Id,
    Integer,
    Logical,
    Percentage,
    Text,
)


@structure
class AnalysisPrecedent(Structure):
    analysis_id: Id
    precedent: Precedent
    is_chosen: Logical
    synthesis: Text | None
    thesis_similarity_score: Decimal
    enunciation_similarity_score: Decimal
    total_search_hits: Integer
    similarity_rank: Integer
    similarity_percentage: Percentage | None
    applicability_level: AnalysisPrecedentApplicabilityLevel

    @classmethod
    def create(cls, dto: AnalysisPrecedentDto) -> 'AnalysisPrecedent':
        return cls(
            analysis_id=Id.create(dto.analysis_id),
            precedent=Precedent.create(dto.precedent),
            similarity_percentage=(
                Percentage.create(dto.similarity_percentage)
                if dto.similarity_percentage is not None
                else None
            ),
            is_chosen=Logical.create(dto.is_chosen),
            synthesis=Text.create(dto.synthesis) if dto.synthesis is not None else None,
            thesis_similarity_score=Decimal.create(dto.thesis_similarity_score),
            enunciation_similarity_score=Decimal.create(dto.enunciation_similarity_score),
            total_search_hits=Integer.create(dto.total_search_hits),
            similarity_rank=Integer.create(dto.similarity_rank),
            applicability_level=AnalysisPrecedentApplicabilityLevel.create(
                dto.applicability_level
                if dto.applicability_level is not None
                else dto.similarity_percentage
            ),
        )

    @property
    def dto(self) -> AnalysisPrecedentDto:
        return AnalysisPrecedentDto(
            analysis_id=self.analysis_id.value,
            precedent=self.precedent.dto,
            synthesis=self.synthesis.value if self.synthesis is not None else None,
            similarity_percentage=(
                self.similarity_percentage.value
                if self.similarity_percentage is not None
                else None
            ),
            is_chosen=self.is_chosen.value,
            thesis_similarity_score=self.thesis_similarity_score.value,
            enunciation_similarity_score=self.enunciation_similarity_score.value,
            total_search_hits=self.total_search_hits.value,
            similarity_rank=self.similarity_rank.value,
            applicability_level=self.applicability_level.dto,
        )
