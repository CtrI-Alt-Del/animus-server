from typing import Protocol

from animus.core.intake.domain.entities import Precedent
from animus.core.intake.domain.structures import Court
from animus.core.shared.domain.structures import Integer


class PrecedentsRepository(Protocol):
    def find_by_court_and_number(self, court: Court, number: Integer) -> Precedent: ...

    def add_many(self, precedents: list[Precedent]) -> None: ...
