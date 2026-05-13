from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.errors.analysis_not_found_error import (
    AnalysisNotFoundError,
)
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.use_cases.unarchive_analysis_use_case import (
    UnarchiveAnalysisUseCase,
)
from animus.core.shared.domain.structures import Id
from animus.fakers.intake.entities.analyses_faker import AnalysesFaker


class TestUnarchiveAnalysisUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analisyses_repository_mock = create_autospec(
            AnalisysesRepository,
            instance=True,
        )
        self.use_case = UnarchiveAnalysisUseCase(
            analisyses_repository=self.analisyses_repository_mock,
        )

    def test_should_unarchive_analysis_idempotently_and_persist_it(self) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        account_id = '01BX5ZZKBKACTAV9WEVGEMMVRZ'
        analysis = AnalysesFaker.fake(
            analysis_id=analysis_id,
            account_id=account_id,
            is_archived=False,
        )
        self.analisyses_repository_mock.find_by_id.return_value = analysis

        result = self.use_case.execute(
            account_id=account_id,
            analysis_id=analysis_id,
        )

        self.analisyses_repository_mock.find_by_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        self.analisyses_repository_mock.replace.assert_called_once_with(analysis)
        assert result.is_archived is False

    def test_should_raise_analysis_not_found_error_when_analysis_belongs_to_another_account(
        self,
    ) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        self.analisyses_repository_mock.find_by_id.return_value = AnalysesFaker.fake(
            analysis_id=analysis_id,
            account_id='01BX5ZZKBKACTAV9WEVGEMMVS0',
        )

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(
                account_id='01BX5ZZKBKACTAV9WEVGEMMVRZ',
                analysis_id=analysis_id,
            )

        self.analisyses_repository_mock.replace.assert_not_called()
