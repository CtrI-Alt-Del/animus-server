from animus.core.intake.domain.structures.analysis_precedent_applicability_level import (
    AnalysisPrecedentApplicabilityLevel,
)
from animus.core.intake.domain.structures.dtos.analysis_precedent_dataset_dto import (
    AnalysisPrecedentDatasetDto,
)
from animus.core.intake.domain.structures.precedent_identifier import (
    PrecedentIdentifier,
)
from animus.core.intake.domain.structures.precedent_status import PrecedentStatus
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Datetime, Decimal, Id, Integer, Logical


@structure
class AnalysisPrecedentDatasetRow(Structure):
    analysis_precedent_id: Id
    analysis_id: Id
    created_at: Datetime
    applicability_level: AnalysisPrecedentApplicabilityLevel
    is_from_human: Logical
    thesis_similarity_score: Decimal
    enunciation_similarity_score: Decimal
    total_search_hits: Integer
    similarity_rank: Integer
    identifier: PrecedentIdentifier
    precedent_status: PrecedentStatus
    last_updated_in_pangea_at: Datetime

    @classmethod
    def create(cls, dto: AnalysisPrecedentDatasetDto) -> 'AnalysisPrecedentDatasetRow':
        return cls(
            analysis_precedent_id=Id.create(dto.analysis_precedent_id),
            analysis_id=Id.create(dto.analysis_id),
            created_at=Datetime.create(dto.created_at),
            applicability_level=AnalysisPrecedentApplicabilityLevel.create(
                dto.applicability_level
            ),
            is_from_human=Logical.create(dto.is_from_human),
            thesis_similarity_score=Decimal.create(dto.thesis_similarity_score),
            enunciation_similarity_score=Decimal.create(
                dto.enunciation_similarity_score
            ),
            total_search_hits=Integer.create(dto.total_search_hits),
            similarity_rank=Integer.create(dto.similarity_rank),
            identifier=PrecedentIdentifier.create(dto.identifier),
            precedent_status=PrecedentStatus.create(dto.precedent_status),
            last_updated_in_pangea_at=Datetime.create(dto.last_updated_in_pangea_at),
        )

    @property
    def dto(self) -> AnalysisPrecedentDatasetDto:
        return AnalysisPrecedentDatasetDto(
            analysis_precedent_id=self.analysis_precedent_id.value,
            analysis_id=self.analysis_id.value,
            created_at=self.created_at.value.isoformat(),
            applicability_level=self.applicability_level.dto,
            is_from_human=self.is_from_human.value,
            thesis_similarity_score=self.thesis_similarity_score.value,
            enunciation_similarity_score=self.enunciation_similarity_score.value,
            total_search_hits=self.total_search_hits.value,
            similarity_rank=self.similarity_rank.value,
            identifier=self.identifier.dto,
            precedent_status=self.precedent_status.dto,
            last_updated_in_pangea_at=self.last_updated_in_pangea_at.value.isoformat(),
        )
