from animus.core.intake.domain.structures.analysies_precedent_legal_features import (
    AnalysiesPrecedentLegalFeatures,
)
from animus.core.intake.domain.structures.dtos.analysies_precedent_legal_features_dto import (
    AnalysiesPrecedentLegalFeaturesDto,
)
from animus.database.sqlalchemy.models.intake.analysies_precedent_legal_features_model import (
    AnalysiesPrecedentLegalFeaturesModel,
)


class AnalysiesPrecedentLegalFeaturesMapper:
    @staticmethod
    def to_entity(
        model: AnalysiesPrecedentLegalFeaturesModel,
    ) -> AnalysiesPrecedentLegalFeatures:
        return AnalysiesPrecedentLegalFeatures.create(
            AnalysiesPrecedentLegalFeaturesDto(
                central_issue_match=model.central_issue_match,
                structural_issue_match=model.structural_issue_match,
                context_compatibility=model.context_compatibility,
                is_lateral_topic=model.is_lateral_topic,
                is_accessory_topic=model.is_accessory_topic,
            )
        )

    @staticmethod
    def to_model(
        legal_features: AnalysiesPrecedentLegalFeatures,
        analysis_id: str,
        precedent_id: str,
    ) -> AnalysiesPrecedentLegalFeaturesModel:
        return AnalysiesPrecedentLegalFeaturesModel(
            analysis_id=analysis_id,
            precedent_id=precedent_id,
            central_issue_match=legal_features.central_issue_match.value,
            structural_issue_match=legal_features.structural_issue_match.value,
            context_compatibility=legal_features.context_compatibility.value,
            is_lateral_topic=legal_features.is_lateral_topic.value,
            is_accessory_topic=legal_features.is_accessory_topic.value,
        )
