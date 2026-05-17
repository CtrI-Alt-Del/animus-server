from typing import Protocol

from animus.core.intake.domain.structures import CaseSummaryEmbedding
from animus.core.intake.domain.structures.case_summary import CaseSummary


class CaseSummaryEmbeddingsProvider(Protocol):
    def generate(self, case_summary: CaseSummary) -> list[CaseSummaryEmbedding]: ...
