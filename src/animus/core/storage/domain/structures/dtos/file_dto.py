from animus.core.shared.domain.decorators import dto


@dto
class FileDto:
    value: bytes
    key: str
    size_in_bytes: float
    mime_type: str
