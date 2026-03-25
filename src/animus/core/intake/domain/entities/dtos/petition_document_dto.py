from animus.core.shared.domain.decorators import dto


@dto
class PetitionDocumentDto:
    file_path: str
    name: str
