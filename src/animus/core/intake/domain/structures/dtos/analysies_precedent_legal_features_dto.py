from animus.core.shared.domain.decorators import dto


@dto
class AnalysiesPrecedentLegalFeaturesDto:
    central_issue_match: int
    structural_issue_match: int
    context_compatibility: int
    is_lateral_topic: int
    is_accessory_topic: int
