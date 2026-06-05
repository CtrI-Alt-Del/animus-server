from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    SecondInstanceAnalysisRequiredError,
)
from animus.core.intake.domain.structures import SecondInstanceDecision
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.dtos import SecondInstanceDecisionDto
from animus.core.intake.domain.structures.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.intake.interfaces import (
    AnalysesRepository,
    SecondInstanceDecisionsRepository,
)
from animus.core.intake.use_cases import CreateSecondInstanceDecisionUseCase
from animus.core.shared.domain.structures import Id


class TestCreateSecondInstanceDecisionUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.second_instance_decisions_repository_mock = create_autospec(
            SecondInstanceDecisionsRepository,
            instance=True,
        )
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository,
            instance=True,
        )
        self.use_case = CreateSecondInstanceDecisionUseCase(
            second_instance_decisions_repository=self.second_instance_decisions_repository_mock,
            analyses_repository=self.analyses_repository_mock,
        )

    def test_should_add_decision_and_update_status_when_decision_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_second_instance().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.second_instance_decisions_repository_mock.find_by_analysis_id.return_value = None

        result = self.use_case.execute(
            analysis_id=analysis_id,
            description='  Dar provimento ao recurso  ',
        )

        self.second_instance_decisions_repository_mock.add.assert_called_once()
        self.second_instance_decisions_repository_mock.replace.assert_not_called()
        self.analyses_repository_mock.replace.assert_called_once_with(analysis)
        assert result == SecondInstanceDecisionDto(
            analysis_id=analysis_id,
            description='Dar provimento ao recurso',
        )
        assert (
            analysis.status
            == SecondInstanceAnalysisStatus.create_as_decision_submitted()
        )

    def test_should_replace_decision_and_update_status_when_decision_exists(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_second_instance().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.second_instance_decisions_repository_mock.find_by_analysis_id.return_value = SecondInstanceDecision.create(
            SecondInstanceDecisionDto(
                analysis_id=analysis_id,
                description='Manter sentença',
            )
        )

        result = self.use_case.execute(
            analysis_id=analysis_id,
            description='Reformar parcialmente a sentença',
        )

        self.second_instance_decisions_repository_mock.add.assert_not_called()
        self.second_instance_decisions_repository_mock.replace.assert_called_once()
        assert result.description == 'Reformar parcialmente a sentença'

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(
                analysis_id=Id.create().value,
                description='Reformar sentença',
            )

    def test_should_raise_second_instance_analysis_required_error_when_analysis_is_not_second_instance(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_first_instance().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis

        with pytest.raises(SecondInstanceAnalysisRequiredError):
            self.use_case.execute(
                analysis_id=analysis_id,
                description='Reformar sentença',
            )

        self.second_instance_decisions_repository_mock.find_by_analysis_id.assert_not_called()

    @staticmethod
    def _create_analysis(analysis_id: str, analysis_type: str) -> Analysis:
        return Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Análise',
                folder_id=None,
                account_id=Id.create().value,
                type=analysis_type,
                status='CASE_ANALYZED',
                is_archived=False,
                created_at='2026-06-04T10:30:00+00:00',
            )
        )
