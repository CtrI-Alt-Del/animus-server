from animus.core.intake.domain.structures.dtos.petition_summary_embedding_dto import (
    PetitionSummaryEmbeddingDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Decimal, Text


@structure
class PetitionSummaryEmbedding(Structure):
    vector: list[Decimal]
    chunk: Text

    @classmethod
    def create(cls, vector: list[Decimal], chunk: Text) -> 'PetitionSummaryEmbedding':
        return cls(vector=vector, chunk=chunk)

    @property
    def dto(self) -> PetitionSummaryEmbeddingDto:
        return PetitionSummaryEmbeddingDto(
            vector=[item.value for item in self.vector],
            chunk=self.chunk.value,
        )
