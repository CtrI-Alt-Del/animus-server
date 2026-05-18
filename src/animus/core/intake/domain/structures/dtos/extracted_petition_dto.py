from animus.core.shared.domain.decorators import dto


@dto
class ExtractedPetitionDto:
    analysis_id: str
    first_page: int
    last_page: int
