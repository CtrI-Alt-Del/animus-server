from animus.core.shared.domain.decorators import dto


@dto
class PetitionDocumentDto:
    file_key: str
    name: str
