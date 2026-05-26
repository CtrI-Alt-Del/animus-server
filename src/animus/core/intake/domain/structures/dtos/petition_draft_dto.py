from animus.core.shared.domain.decorators import dto


@dto
class PetitionDraftDto:
    analysis_id: str
    structured_facts: str
    legal_grounds: str
    central_thesis: str
    requests: list[str]
    precedent_citations: list[str]
