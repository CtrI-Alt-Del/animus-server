from animus.core.intake.domain.structures.dtos.petition_embedding_dto import PetitionEmbeddingDto
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.structures import Decimal, Text


@structure
class PetitionEmbedding(Structure):
    vector: list[Decimal]
    chunk: Text

    @classmethod
    def create(cls, vector: list[Decimal], chunk: Text) -> 'PetitionEmbedding':
        return cls(vector=vector, chunk=chunk)

    @property
    def dto(self) -> PetitionEmbeddingDto:
        return PetitionEmbeddingDto(
            vector=[item.value for item in self.vector],
            chunk=self.chunk.value,
        )
