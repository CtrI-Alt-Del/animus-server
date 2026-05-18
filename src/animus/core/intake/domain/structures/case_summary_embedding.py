from animus.core.intake.domain.structures.dtos.petition_summary_embedding_dto import (
    CaseSummaryEmbeddingDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Decimal, Text


@structure
class CaseSummaryEmbedding(Structure):
    vector: list[Decimal]
    chunk: Text

    @classmethod
    def create(cls, vector: list[Decimal], chunk: Text) -> 'CaseSummaryEmbedding':
        return cls(vector=vector, chunk=chunk)

    @property
    def dto(self) -> CaseSummaryEmbeddingDto:
        return CaseSummaryEmbeddingDto(
            vector=[item.value for item in self.vector],
            chunk=self.chunk.value,
        )
