from animus.core.intake.domain.structures.dtos.second_instance_decision_dto import (
    SecondInstanceDecisionDto,
)
from animus.core.intake.domain.structures.second_instance_decision import (
    SecondInstanceDecision,
)
from animus.database.sqlalchemy.models.intake.second_instance_decision_model import (
    SecondInstanceDecisionModel,
)


class SecondInstanceDecisionMapper:
    @staticmethod
    def to_entity(model: SecondInstanceDecisionModel) -> SecondInstanceDecision:
        return SecondInstanceDecision.create(
            SecondInstanceDecisionDto(
                analysis_id=model.analysis_id,
                description=model.description,
            )
        )

    @staticmethod
    def to_model(
        decision: SecondInstanceDecision,
    ) -> SecondInstanceDecisionModel:
        return SecondInstanceDecisionModel(
            analysis_id=decision.analysis_id.value,
            description=decision.description.value,
        )
