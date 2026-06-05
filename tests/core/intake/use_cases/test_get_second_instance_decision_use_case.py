from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.errors import SecondInstanceDecisionNotFoundError
from animus.core.intake.domain.structures import SecondInstanceDecision
from animus.core.intake.domain.structures.dtos import SecondInstanceDecisionDto
from animus.core.intake.interfaces import SecondInstanceDecisionsRepository
from animus.core.intake.use_cases import GetSecondInstanceDecisionUseCase
from animus.core.shared.domain.structures import Id


class TestGetSecondInstanceDecisionUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.second_instance_decisions_repository_mock = create_autospec(
            SecondInstanceDecisionsRepository,
            instance=True,
        )
        self.use_case = GetSecondInstanceDecisionUseCase(
            second_instance_decisions_repository=self.second_instance_decisions_repository_mock,
        )

    def test_should_return_decision_dto_when_decision_exists(self) -> None:
        analysis_id = Id.create().value
        decision = SecondInstanceDecision.create(
            SecondInstanceDecisionDto(
                analysis_id=analysis_id,
                description='Dar provimento ao recurso',
            )
        )
        self.second_instance_decisions_repository_mock.find_by_analysis_id.return_value = decision

        result = self.use_case.execute(analysis_id=analysis_id)

        assert result == decision.dto()

    def test_should_raise_not_found_error_when_decision_does_not_exist(self) -> None:
        self.second_instance_decisions_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(SecondInstanceDecisionNotFoundError):
            self.use_case.execute(analysis_id=Id.create().value)
