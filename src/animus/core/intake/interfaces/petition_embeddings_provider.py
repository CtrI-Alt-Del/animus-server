from typing import Protocol

from animus.core.intake.domain.entities import Petition
from animus.core.intake.domain.structures import PetitionEmbedding


class PetitionEmbeddingsProvider(Protocol):
    def generate(self, petition: Petition) -> list[PetitionEmbedding]: ...
