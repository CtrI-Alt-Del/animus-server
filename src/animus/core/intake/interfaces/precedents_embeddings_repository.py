from typing import Protocol

from animus.core.intake.domain.structures.petition_embedding import PetitionEmbedding
from animus.core.intake.domain.structures.precedent_embedding import PrecedentEmbedding
from animus.core.shared.responses import ListResponse


class PrecedentsEmbeddingsRepository(Protocol):
    def find_many(
        self,
        petition_embeddings: list[PetitionEmbedding],
    ) -> ListResponse[PrecedentEmbedding]: ...

    def add_many(self, precedents_embeddings: list[PrecedentEmbedding]) -> None: ...
