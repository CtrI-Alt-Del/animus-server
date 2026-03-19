from animus.core.shared.domain.decorators import dto


@dto
class PetitionEmbeddingDto:
    vector: list[float]
    chunk: str
