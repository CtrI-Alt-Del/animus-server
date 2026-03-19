from animus.core.shared.domain.decorators import dto


@dto
class PrecedentEmbeddingDto:
    score: float
    vector: list[float]
    field: str
    court: str
    number: int
    chunk: str
