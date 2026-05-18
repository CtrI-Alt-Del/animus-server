from typing import Protocol

from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.shared.domain.structures import Id


class CaseSummariesRepository(Protocol):
    def find_by_analysis_id(self, analysis_id: Id) -> CaseSummary | None: ...

    def add(self, analysis_id: Id, case_summary: CaseSummary) -> None: ...

    def replace(self, analysis_id: Id, case_summary: CaseSummary) -> None: ...
