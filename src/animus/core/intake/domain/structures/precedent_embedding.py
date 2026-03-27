from animus.core.intake.domain.structures.court import Court
from animus.core.intake.domain.structures.dtos.precedent_embedding_dto import PrecedentEmbeddingDto
from animus.core.intake.domain.structures.precedent_embedding_field import (
    PrecedentEmbeddingField,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Decimal, Integer, Text


@structure
class PrecedentEmbedding(Structure):
    score: Decimal
    vector: list[Decimal]
    field: PrecedentEmbeddingField
    court: Court
    number: Integer
    chunk: Text

    @classmethod
    def create(
        cls,
        score: Decimal,
        vector: list[Decimal],
        field: PrecedentEmbeddingField,
        court: Court,
        number: Integer,
        chunk: Text,
    ) -> 'PrecedentEmbedding':
        return cls(
            score=score,
            vector=vector,
            field=field,
            court=court,
            number=number,
            chunk=chunk,
        )

    @property
    def dto(self) -> PrecedentEmbeddingDto:
        return PrecedentEmbeddingDto(
            score=self.score.value,
            vector=[item.value for item in self.vector],
            field=self.field.dto,
            court=self.court.dto,
            number=self.number.value,
            chunk=self.chunk.value,
        )
