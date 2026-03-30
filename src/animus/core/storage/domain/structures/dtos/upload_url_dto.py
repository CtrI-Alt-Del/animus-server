from animus.core.shared.domain.decorators import dto
from animus.core.shared.domain.structures import FilePath


@dto
class UploadUrlDto:
    url: str
    token: str
    file_path: FilePath | str
