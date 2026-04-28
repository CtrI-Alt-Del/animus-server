from unittest.mock import create_autospec

import pytest

from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.use_cases.list_analyses_use_case import ListAnalysesUseCase
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id, Integer, Logical, Text
from animus.core.shared.responses import CursorPaginationResponse
from animus.fakers.intake.entities.analyses_faker import AnalysesFaker


class TestListAnalysesUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analisyses_repository_mock = create_autospec(
            AnalisysesRepository,
            instance=True,
        )
        self.use_case = ListAnalysesUseCase(
            analisyses_repository=self.analisyses_repository_mock,
        )

    def test_should_list_analyses_from_repository_and_return_dtos(self) -> None:
        analysis = AnalysesFaker.fake(
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
            account_id='01BX5ZZKBKACTAV9WEVGEMMVRZ',
            name='Analise trabalhista',
        )
        next_cursor = Id.create('01BX5ZZKBKACTAV9WEVGEMMVS0')
        self.analisyses_repository_mock.find_many.return_value = (
            CursorPaginationResponse(items=[analysis], next_cursor=next_cursor)
        )

        result = self.use_case.execute(
            account_id='01BX5ZZKBKACTAV9WEVGEMMVRZ',
            search='trabalhista',
            cursor='01BX5ZZKBKACTAV9WEVGEMMVS1',
            limit=10,
            is_archived=False,
        )

        self.analisyses_repository_mock.find_many.assert_called_once_with(
            account_id=Id.create('01BX5ZZKBKACTAV9WEVGEMMVRZ'),
            search=Text.create('trabalhista'),
            cursor=Id.create('01BX5ZZKBKACTAV9WEVGEMMVS1'),
            limit=Integer.create(10),
            is_archived=Logical.create_false(),
            only_unfoldered=Logical.create_false(),
        )
        assert result.items == [analysis.dto]
        assert result.next_cursor == next_cursor

    def test_should_raise_validation_error_when_cursor_is_invalid(self) -> None:
        with pytest.raises(ValidationError, match=r'ULID invalido|ULID inválido'):
            self.use_case.execute(
                account_id='01BX5ZZKBKACTAV9WEVGEMMVRZ',
                search='',
                cursor='invalid-cursor',
                limit=10,
                is_archived=False,
            )

        self.analisyses_repository_mock.find_many.assert_not_called()

    def test_should_raise_validation_error_when_limit_is_not_positive(self) -> None:
        with pytest.raises(
            ValidationError,
            match='Valor deve ser maior ou igual a 1, recebido: 0',
        ):
            self.use_case.execute(
                account_id='01BX5ZZKBKACTAV9WEVGEMMVRZ',
                search='',
                cursor=None,
                limit=0,
                is_archived=False,
            )

        self.analisyses_repository_mock.find_many.assert_not_called()
