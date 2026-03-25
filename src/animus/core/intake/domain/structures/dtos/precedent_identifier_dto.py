from animus.core.shared.domain.decorators import dto


@dto
class PrecedentIdentifierDto:
    court: str
    kind: str
    number: int
