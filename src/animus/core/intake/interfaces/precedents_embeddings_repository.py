from typing import Protocol

from animus.core.intake.domain.structures.analysis_precedents_search_filters import (
    AnalysisPrecedentsSearchFilters,
)

from animus.core.intake.domain.structures.case_summary_embedding import (
    CaseSummaryEmbedding,
)
from animus.core.intake.domain.structures.precedent_embedding import PrecedentEmbedding
from animus.core.shared.domain.structures import Integer
from animus.core.shared.responses import ListResponse


class PrecedentsEmbeddingsRepository(Protocol):
    def find_many(
        self,
        case_summary_embeddings: list[CaseSummaryEmbedding],
        filters: AnalysisPrecedentsSearchFilters,
        limit: Integer,
    ) -> ListResponse[PrecedentEmbedding]: ...

    def add_many(self, precedents_embeddings: list[PrecedentEmbedding]) -> None: ...
