from typing import Protocol

from animus.core.intake.domain.structures.petition_draft import PetitionDraft
from animus.core.shared.domain.structures import Id


class PetitionDraftsRepository(Protocol):
    def find_by_analysis_id(self, analysis_id: Id) -> PetitionDraft | None: ...

    def add(self, petition_draft: PetitionDraft) -> None: ...

    def replace(self, petition_draft: PetitionDraft) -> None: ...
