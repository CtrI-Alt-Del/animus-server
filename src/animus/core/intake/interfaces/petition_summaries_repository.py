from typing import Protocol

from animus.core.intake.domain.structures.petition_summary import PetitionSummary
from animus.core.shared.domain.structures import Id


class PetitionSummariesRepository(Protocol):
    def find_by_petition_id(self, petition_id: Id) -> PetitionSummary | None: ...

    def find_by_analysis_id(self, analysis_id: Id) -> PetitionSummary | None: ...

    def add(self, petition_id: Id, petition_summary: PetitionSummary) -> None: ...

    def replace(self, petition_id: Id, petition_summary: PetitionSummary) -> None: ...
