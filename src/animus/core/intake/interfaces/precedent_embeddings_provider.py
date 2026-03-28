from typing import Protocol

from animus.core.intake.domain.entities.precedent import Precedent
from animus.core.intake.domain.structures.precedent_embedding import PrecedentEmbedding


class PrecedentEmbeddingsProvider(Protocol):
    def generate(self, precedents: list[Precedent]) -> list[PrecedentEmbedding]: ...
