from typing import Protocol

from animus.core.intake.domain.structures.petition_summary_embedding import (
    PetitionSummaryEmbedding,
)
from animus.core.intake.domain.structures.petition_summary import PetitionSummary


class PetitionSummaryEmbeddingsProvider(Protocol):
    def generate(
        self, petition_summary: PetitionSummary
    ) -> list[PetitionSummaryEmbedding]: ...
