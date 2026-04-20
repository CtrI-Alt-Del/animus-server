from animus.core.intake.domain.structures import AnalysisPrecedent
from animus.core.intake.domain.structures.dtos import AnalysisPrecedentDto
from animus.database.sqlalchemy.mappers.intake.precedents_mapper import PrecedentMapper
from animus.database.sqlalchemy.models.intake.analysis_precedent_model import (
    AnalysisPrecedentModel,
)


class AnalysisPrecedentMapper:
    @staticmethod
    def to_entity(model: AnalysisPrecedentModel) -> AnalysisPrecedent:
        return AnalysisPrecedent.create(
            AnalysisPrecedentDto(
                analysis_id=model.analysis_id,
                precedent=PrecedentMapper.to_entity(model.precedent).dto,
                is_chosen=model.is_chosen,
                similarity_percentage=model.similarity_percentage,
                thesis_similarity_score=model.thesis_similarity_score,
                enunciation_similarity_score=model.enunciation_similarity_score,
                total_search_hits=model.total_search_hits,
                similarity_rank=model.similarity_rank,
                applicability_level=model.applicability_level,
                synthesis=model.synthesis,
            )
        )

    @staticmethod
    def to_model(entity: AnalysisPrecedent) -> AnalysisPrecedentModel:
        return AnalysisPrecedentModel(
            analysis_id=entity.analysis_id.value,
            precedent_id=entity.precedent.id.value,
            is_chosen=entity.is_chosen.value,
            similarity_percentage=(
                entity.similarity_percentage.value
                if entity.similarity_percentage is not None
                else None
            ),
            thesis_similarity_score=entity.thesis_similarity_score.value,
            enunciation_similarity_score=entity.enunciation_similarity_score.value,
            total_search_hits=entity.total_search_hits.value,
            similarity_rank=entity.similarity_rank.value,
            applicability_level=entity.applicability_level.dto,
            synthesis=entity.synthesis.value if entity.synthesis is not None else None,
        )
