from typing import Protocol

from animus.core.intake.domain.entities.petition import Petition
from animus.core.shared.domain.structures import FilePath, Id
from animus.core.shared.responses import ListResponse


class PetitionsRepository(Protocol):
    def find_by_id(self, petition_id: Id) -> Petition | None: ...

    def find_by_analysis_id(self, analysis_id: Id) -> Petition | None: ...

    def find_by_document_file_path(self, file_path: FilePath) -> Petition | None: ...

    def find_all_by_analysis_id_ordered_by_uploaded_at(
        self,
        analysis_id: Id,
    ) -> ListResponse[Petition]: ...

    def add(self, petition: Petition) -> None: ...

    def add_many(self, petitions: list[Petition]) -> None: ...

    def remove(self, petition_id: Id) -> None: ...
