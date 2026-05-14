from typing import Protocol

from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.petition_summary_embedding import (
    PetitionSummaryEmbedding,
)


class CaseSummaryEmbeddingsProvider(Protocol):
    def generate(self, case_summary: CaseSummary) -> list[PetitionSummaryEmbedding]: ...
