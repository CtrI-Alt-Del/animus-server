from animus.core.shared.domain.decorators import dto


@dto
class PetitionSummaryEmbeddingDto:
    vector: list[float]
    chunk: str
