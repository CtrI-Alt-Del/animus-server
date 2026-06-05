from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    SecondInstanceAnalysisRequiredError,
)
from animus.core.intake.domain.structures import SecondInstanceDecision
from animus.core.intake.domain.structures.dtos import SecondInstanceDecisionDto
from animus.core.intake.domain.structures.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.intake.interfaces import (
    AnalysesRepository,
    SecondInstanceDecisionsRepository,
)
from animus.core.shared.domain.structures import Id


class CreateSecondInstanceDecisionUseCase:
    def __init__(
        self,
        second_instance_decisions_repository: SecondInstanceDecisionsRepository,
        analyses_repository: AnalysesRepository,
    ) -> None:
        self._second_instance_decisions_repository = (
            second_instance_decisions_repository
        )
        self._analyses_repository = analyses_repository

    def execute(self, analysis_id: str, description: str) -> SecondInstanceDecisionDto:
        analysis_id_entity = Id.create(analysis_id)
        analysis = self._analyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.type.is_second_instance.is_false:
            raise SecondInstanceAnalysisRequiredError

        decision = SecondInstanceDecision.create(
            SecondInstanceDecisionDto(
                analysis_id=analysis_id_entity.value,
                description=description,
            )
        )

        existing_decision = (
            self._second_instance_decisions_repository.find_by_analysis_id(
                analysis_id_entity
            )
        )
        if existing_decision is None:
            self._second_instance_decisions_repository.add(decision)
        else:
            self._second_instance_decisions_repository.replace(decision)

        analysis.set_status(SecondInstanceAnalysisStatus.create_as_decision_submitted())
        self._analyses_repository.replace(analysis)

        return decision.dto()
