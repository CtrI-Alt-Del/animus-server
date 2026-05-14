from animus.core.shared.domain.decorators import dto


@dto
class PetitionExtractionDto:
    first_page: int
    last_page: int
