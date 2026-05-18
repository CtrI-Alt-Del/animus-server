from animus.core.shared.domain.decorators import dto


@dto
class PetitionDraftDto:
    analysis_id: str
    content: str
