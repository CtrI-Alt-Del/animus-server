from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.errors.analysis_not_found_error import (
    AnalysisNotFoundError,
)
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.use_cases.rename_analysis_use_case import RenameAnalysisUseCase
from animus.core.shared.domain.structures import Id
from animus.fakers.intake.entities.analyses_faker import AnalysesFaker


class TestRenameAnalysisUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analisyses_repository_mock = create_autospec(
            AnalisysesRepository,
            instance=True,
        )
        self.use_case = RenameAnalysisUseCase(
            analisyses_repository=self.analisyses_repository_mock,
        )

    def test_should_rename_analysis_and_persist_it(self) -> None:
        analysis = AnalysesFaker.fake(
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
            account_id='01BX5ZZKBKACTAV9WEVGEMMVRZ',
        )
        self.analisyses_repository_mock.find_by_id.return_value = analysis

        result = self.use_case.execute(
            account_id='01BX5ZZKBKACTAV9WEVGEMMVRZ',
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
            name='  Analise renomeada  ',
        )

        self.analisyses_repository_mock.find_by_id.assert_called_once_with(
            Id.create('01ARZ3NDEKTSV4RRFFQ69G5FAV')
        )
        self.analisyses_repository_mock.replace.assert_called_once_with(analysis)
        assert result.name == 'Analise renomeada'

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        self.analisyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(
                account_id='01BX5ZZKBKACTAV9WEVGEMMVRZ',
                analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
                name='Analise renomeada',
            )

        self.analisyses_repository_mock.replace.assert_not_called()
