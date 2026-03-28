from animus.core.intake.domain.structures.dtos.precedent_identifier_dto import (
    PrecedentIdentifierDto,
)
from animus.core.shared.domain.decorators import dto


@dto
class PrecedentEmbeddingDto:
    score: float
    vector: list[float]
    field: str
    identifier: PrecedentIdentifierDto
    chunk: str
