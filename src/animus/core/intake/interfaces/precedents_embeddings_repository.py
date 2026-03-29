from typing import Protocol

from animus.core.intake.domain.structures.petition_embedding import (
    PetitionSummaryEmbedding,
)
from animus.core.intake.domain.structures.precedent_embedding import PrecedentEmbedding
from animus.core.shared.responses import ListResponse


class PrecedentsEmbeddingsRepository(Protocol):
    def find_many(
        self,
        petition_summary_embeddings: list[PetitionSummaryEmbedding],
    ) -> ListResponse[PrecedentEmbedding]: ...

    def add_many(self, precedents_embeddings: list[PrecedentEmbedding]) -> None: ...
