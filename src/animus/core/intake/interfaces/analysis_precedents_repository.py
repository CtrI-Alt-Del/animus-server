from typing import Protocol

from animus.core.intake.domain.structures import AnalysisPrecedent
from animus.core.shared.domain.structures import Id
from animus.core.shared.responses import ListResponse


class AnalysisPrecedentsRepository(Protocol):
    def find_many_by_analysis_id(self, analysis_id: Id) -> ListResponse[AnalysisPrecedent]: ...

    def find_by_analysis_id_and_precedent_id(
        self,
        analysis_id: Id,
        precedent_id: Id,
    ) -> AnalysisPrecedent | None: ...

    def remove_many_by_analysis_id(self, analysis_id: Id) -> None: ...

    def add_many_by_analysis_id(
        self,
        analysis_id: Id,
        analysis_precedents: list[AnalysisPrecedent],
    ) -> None: ...

    def choose_by_analysis_id_and_precedent_id(
        self,
        analysis_id: Id,
        precedent_id: Id,
    ) -> None: ...
