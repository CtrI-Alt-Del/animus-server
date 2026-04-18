from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.errors.analysis_not_found_error import (
    AnalysisNotFoundError,
)
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.use_cases.update_analysis_status_use_case import (
    UpdateAnalysisStatusUseCase,
)
from animus.core.shared.domain.structures import Id
from animus.fakers.intake.entities.analyses_faker import AnalysesFaker


class TestUpdateAnalysisStatusUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analisyses_repository_mock = create_autospec(
            AnalisysesRepository,
            instance=True,
        )
        self.use_case = UpdateAnalysisStatusUseCase(
            analisyses_repository=self.analisyses_repository_mock,
        )

    def test_should_update_analysis_status_and_persist_when_analysis_exists(
        self,
    ) -> None:
        analysis = AnalysesFaker.fake(
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
            status='WAITING_PETITION',
        )
        self.analisyses_repository_mock.find_by_id.return_value = analysis

        self.use_case.execute(
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
            status='SEARCHING_PRECEDENTS',
        )

        self.analisyses_repository_mock.find_by_id.assert_called_once_with(
            Id.create('01ARZ3NDEKTSV4RRFFQ69G5FAV')
        )
        self.analisyses_repository_mock.replace.assert_called_once_with(analysis)
        assert analysis.status.value.value == 'SEARCHING_PRECEDENTS'

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        self.analisyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(
                analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
                status='FAILED',
            )

        self.analisyses_repository_mock.replace.assert_not_called()
