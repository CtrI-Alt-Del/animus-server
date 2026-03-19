from typing import Protocol

from animus.core.intake.domain.entities import Precedent
from animus.core.intake.domain.structures import PrecedentEmbedding


class PrecedentEmbeddingsProvider(Protocol):
    def generate(self, precedents: list[Precedent]) -> list[PrecedentEmbedding]: ...
