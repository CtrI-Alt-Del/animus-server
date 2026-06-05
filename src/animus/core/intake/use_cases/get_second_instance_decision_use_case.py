from animus.core.intake.domain.errors import SecondInstanceDecisionNotFoundError
from animus.core.intake.domain.structures.dtos import SecondInstanceDecisionDto
from animus.core.intake.interfaces import SecondInstanceDecisionsRepository
from animus.core.shared.domain.structures import Id


class GetSecondInstanceDecisionUseCase:
    def __init__(
        self,
        second_instance_decisions_repository: SecondInstanceDecisionsRepository,
    ) -> None:
        self._second_instance_decisions_repository = (
            second_instance_decisions_repository
        )

    def execute(self, analysis_id: str) -> SecondInstanceDecisionDto:
        analysis_id_entity = Id.create(analysis_id)
        decision = self._second_instance_decisions_repository.find_by_analysis_id(
            analysis_id_entity,
        )

        if decision is None:
            raise SecondInstanceDecisionNotFoundError

        return decision.dto()
