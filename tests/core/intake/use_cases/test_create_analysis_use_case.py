from unittest.mock import create_autospec

import pytest

from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.use_cases.create_analysis_use_case import CreateAnalysisUseCase
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id, Integer


class TestCreateAnalysisUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analisyses_repository_mock = create_autospec(
            AnalisysesRepository,
            instance=True,
        )
        self.use_case = CreateAnalysisUseCase(
            analisyses_repository=self.analisyses_repository_mock,
        )

    def test_should_create_analysis_with_generated_name_and_add_it_to_repository(
        self,
    ) -> None:
        self.analisyses_repository_mock.find_next_generated_name_number.return_value = (
            Integer.create(3)
        )

        result = self.use_case.execute(
            account_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
            folder_id='01BX5ZZKBKACTAV9WEVGEMMVRZ',
        )

        self.analisyses_repository_mock.find_next_generated_name_number.assert_called_once_with(
            Id.create('01ARZ3NDEKTSV4RRFFQ69G5FAV')
        )
        self.analisyses_repository_mock.add.assert_called_once()
        added_analysis = self.analisyses_repository_mock.add.call_args.args[0]

        assert added_analysis.dto == result
        assert result.name == 'Nova analise #3'
        assert result.account_id == '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        assert result.folder_id == '01BX5ZZKBKACTAV9WEVGEMMVRZ'
        assert result.status == 'WAITING_PETITION'
        assert result.is_archived is False
        assert result.id is not None

    def test_should_raise_validation_error_when_folder_id_is_invalid(self) -> None:
        with pytest.raises(ValidationError, match=r'ULID invalido|ULID inválido'):
            self.use_case.execute(
                account_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
                folder_id='invalid-folder-id',
            )

        self.analisyses_repository_mock.find_next_generated_name_number.assert_not_called()
        self.analisyses_repository_mock.add.assert_not_called()
