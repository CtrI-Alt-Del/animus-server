from animus.core.shared.domain.decorators import dto


@dto
class UploadUrlDto:
    url: str
    token: str
    file_path: str
