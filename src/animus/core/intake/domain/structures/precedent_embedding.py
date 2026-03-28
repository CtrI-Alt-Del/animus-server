from animus.core.intake.domain.structures.dtos.precedent_embedding_dto import (
    PrecedentEmbeddingDto,
)
from animus.core.intake.domain.structures.precedent_embedding_field import (
    PrecedentEmbeddingField,
)
from animus.core.intake.domain.structures.precedent_identifier import (
    PrecedentIdentifier,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Decimal, Text


@structure
class PrecedentEmbedding(Structure):
    score: Decimal
    vector: list[Decimal]
    field: PrecedentEmbeddingField
    identifier: PrecedentIdentifier
    chunk: Text

    @classmethod
    def create(cls, dto: PrecedentEmbeddingDto) -> 'PrecedentEmbedding':
        return cls(
            score=Decimal.create(dto.score),
            vector=[Decimal.create(value) for value in dto.vector],
            field=PrecedentEmbeddingField.create(dto.field),
            identifier=PrecedentIdentifier.create(dto.identifier),
            chunk=Text.create(dto.chunk),
        )

    @property
    def dto(self) -> PrecedentEmbeddingDto:
        return PrecedentEmbeddingDto(
            score=self.score.value,
            vector=[item.value for item in self.vector],
            field=self.field.dto,
            identifier=self.identifier.dto,
            chunk=self.chunk.value,
        )
