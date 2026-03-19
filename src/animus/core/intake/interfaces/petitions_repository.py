from typing import Protocol

from animus.core.intake.domain.entities import Petition
from animus.core.shared.domain.structures import Id
from animus.core.shared.responses import ListResponse


class PetitionsRepository(Protocol):
    def find_all_by_analysis_id_ordered_by_uploaded_at(
        self,
        analysis_id: Id,
    ) -> ListResponse[Petition]: ...

    def add(self, petition: Petition) -> None: ...

    def add_many(self, petitions: list[Petition]) -> None: ...
