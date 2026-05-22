from animus.core.shared.domain.decorators import dto


@dto
class CaseSummaryEmbeddingDto:
    vector: list[float]
    chunk: str
