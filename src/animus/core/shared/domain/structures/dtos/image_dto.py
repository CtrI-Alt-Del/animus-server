from animus.core.shared.domain.decorators.dto import dto


@dto
class ImageDto:
    key: str
    name: str
