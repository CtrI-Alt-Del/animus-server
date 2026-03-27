from typing import Protocol

from animus.core.intake.domain.entities.petition import Petition
from animus.core.intake.domain.structures.petition_embedding import PetitionEmbedding



class PetitionEmbeddingsProvider(Protocol):
    def generate(self, petition: Petition) -> list[PetitionEmbedding]: ...
