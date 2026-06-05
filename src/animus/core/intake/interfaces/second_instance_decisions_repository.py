from typing import Protocol

from animus.core.intake.domain.structures.second_instance_decision import (
    SecondInstanceDecision,
)
from animus.core.shared.domain.structures import Id


class SecondInstanceDecisionsRepository(Protocol):
    def find_by_analysis_id(self, analysis_id: Id) -> SecondInstanceDecision | None: ...

    def add(self, decision: SecondInstanceDecision) -> None: ...

    def replace(self, decision: SecondInstanceDecision) -> None: ...
