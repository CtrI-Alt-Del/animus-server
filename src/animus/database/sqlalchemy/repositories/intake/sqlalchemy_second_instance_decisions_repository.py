from sqlalchemy.orm import Session

from animus.core.intake.domain.structures.second_instance_decision import (
    SecondInstanceDecision,
)
from animus.core.intake.interfaces.second_instance_decisions_repository import (
    SecondInstanceDecisionsRepository,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.mappers.intake.second_instance_decision_mapper import (
    SecondInstanceDecisionMapper,
)
from animus.database.sqlalchemy.models.intake.second_instance_decision_model import (
    SecondInstanceDecisionModel,
)


class SqlalchemySecondInstanceDecisionsRepository(SecondInstanceDecisionsRepository):
    def __init__(self, sqlalchemy: Session) -> None:
        self._sqlalchemy = sqlalchemy

    def find_by_analysis_id(self, analysis_id: Id) -> SecondInstanceDecision | None:
        model = self._sqlalchemy.get(SecondInstanceDecisionModel, analysis_id.value)
        if model is None:
            return None

        return SecondInstanceDecisionMapper.to_entity(model)

    def add(self, decision: SecondInstanceDecision) -> None:
        self._sqlalchemy.add(SecondInstanceDecisionMapper.to_model(decision))

    def replace(self, decision: SecondInstanceDecision) -> None:
        model = self._sqlalchemy.get(
            SecondInstanceDecisionModel,
            decision.analysis_id.value,
        )
        if model is None:
            self.add(decision)
            return

        model.description = decision.description.value
