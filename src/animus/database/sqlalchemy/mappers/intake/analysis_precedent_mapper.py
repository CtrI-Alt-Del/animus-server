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
                applicability_percentage=model.applicability_percentage,
                synthesis=model.synthesis,
            )
        )

    @staticmethod
    def to_model(entity: AnalysisPrecedent) -> AnalysisPrecedentModel:
        return AnalysisPrecedentModel(
            analysis_id=entity.analysis_id.value,
            precedent_id=entity.precedent.id.value,
            is_chosen=entity.is_chosen.value,
            applicability_percentage=(
                entity.applicability_percentage.value
                if entity.applicability_percentage is not None
                else None
            ),
            synthesis=entity.synthesis.value if entity.synthesis is not None else None,
        )
