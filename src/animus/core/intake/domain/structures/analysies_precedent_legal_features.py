from animus.core.intake.domain.structures.dtos.analysies_precedent_legal_features_dto import (
    AnalysiesPrecedentLegalFeaturesDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Integer


@structure
class AnalysiesPrecedentLegalFeatures(Structure):
    central_issue_match: Integer
    structural_issue_match: Integer
    context_compatibility: Integer
    is_lateral_topic: Integer
    is_accessory_topic: Integer

    @classmethod
    def create(
        cls,
        dto: AnalysiesPrecedentLegalFeaturesDto,
    ) -> 'AnalysiesPrecedentLegalFeatures':
        return cls(
            central_issue_match=Integer.create(dto.central_issue_match),
            structural_issue_match=Integer.create(dto.structural_issue_match),
            context_compatibility=Integer.create(dto.context_compatibility),
            is_lateral_topic=Integer.create(dto.is_lateral_topic),
            is_accessory_topic=Integer.create(dto.is_accessory_topic),
        )

    @property
    def dto(self) -> AnalysiesPrecedentLegalFeaturesDto:
        return AnalysiesPrecedentLegalFeaturesDto(
            central_issue_match=self.central_issue_match.value,
            structural_issue_match=self.structural_issue_match.value,
            context_compatibility=self.context_compatibility.value,
            is_lateral_topic=self.is_lateral_topic.value,
            is_accessory_topic=self.is_accessory_topic.value,
        )
