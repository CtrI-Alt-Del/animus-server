from animus.core.shared.domain.decorators import dto


@dto
class SecondInstanceDecisionDto:
    analysis_id: str
    description: str
