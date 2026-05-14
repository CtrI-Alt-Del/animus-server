from typing import Protocol

from animus.core.intake.domain.structures.extracted_petition import ExtractedPetition
from animus.core.shared.domain.structures import Id


class ExtractedPetitionsRepository(Protocol):
    def find_by_analysis_id(self, analysis_id: Id) -> ExtractedPetition | None: ...

    def add(self, extracted_petition: ExtractedPetition) -> None: ...

    def replace(self, extracted_petition: ExtractedPetition) -> None: ...
