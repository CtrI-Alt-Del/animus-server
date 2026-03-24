from typing import Protocol

from animus.core.intake.domain.entities import Precedent
from animus.core.intake.domain.structures import Court
from animus.core.intake.domain.structures.precedent_identifier import (
    PrecedentIdentifier,
)
from animus.core.shared.domain.structures import Integer


class PrecedentsRepository(Protocol):
    def find_by_id(self, court: Court, number: Integer) -> Precedent: ...

    def add_many(self, precedents: list[Precedent]) -> None: ...

    def find_all_identifiers(self) -> set[PrecedentIdentifier]: ...
