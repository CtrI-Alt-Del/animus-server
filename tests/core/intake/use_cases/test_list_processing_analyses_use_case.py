from unittest.mock import create_autospec

import pytest

from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.use_cases.list_processing_analyses_use_case import (
    ListProcessingAnalysesUseCase,
)
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id
from animus.fakers.intake.entities.analyses_faker import AnalysesFaker


class TestListProcessingAnalysesUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analisyses_repository_mock = create_autospec(
            AnalisysesRepository,
            instance=True,
        )
        self.use_case = ListProcessingAnalysesUseCase(
            analisyses_repository=self.analisyses_repository_mock,
        )

    def test_should_list_processing_analyses_from_repository_and_return_dtos(
        self,
    ) -> None:
        analysis = AnalysesFaker.fake(
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
            account_id='01BX5ZZKBKACTAV9WEVGEMMVRZ',
            name='Analise em processamento',
        )

        self.analisyses_repository_mock.find_many_in_processing.return_value = [
            analysis
        ]

        result = self.use_case.execute(
            account_id='01BX5ZZKBKACTAV9WEVGEMMVRZ',
        )

        self.analisyses_repository_mock.find_many_in_processing.assert_called_once_with(
            account_id=Id.create('01BX5ZZKBKACTAV9WEVGEMMVRZ'),
        )
        assert result == [analysis.dto]

    def test_should_return_empty_list_when_there_are_no_analyses_in_processing(
        self,
    ) -> None:
        self.analisyses_repository_mock.find_many_in_processing.return_value = []

        result = self.use_case.execute(
            account_id='01BX5ZZKBKACTAV9WEVGEMMVRZ',
        )

        self.analisyses_repository_mock.find_many_in_processing.assert_called_once_with(
            account_id=Id.create('01BX5ZZKBKACTAV9WEVGEMMVRZ'),
        )
        assert result == []

    def test_should_raise_validation_error_when_account_id_is_invalid(self) -> None:
        with pytest.raises(ValidationError, match=r'ULID invalido|ULID inválido'):
            self.use_case.execute(
                account_id='invalid-account-id',
            )

        self.analisyses_repository_mock.find_many_in_processing.assert_not_called()
