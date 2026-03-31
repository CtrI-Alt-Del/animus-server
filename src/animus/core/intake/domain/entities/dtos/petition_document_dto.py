from animus.core.shared.domain.decorators import dto
from animus.core.shared.domain.structures import FilePath


@dto
class PetitionDocumentDto:
    file_path: FilePath | str
    name: str
