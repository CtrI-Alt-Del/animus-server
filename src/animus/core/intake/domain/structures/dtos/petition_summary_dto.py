from animus.core.shared.domain.decorators import dto


@dto
class PetitionSummaryDto:
    content: str
    main_points: list[str]
