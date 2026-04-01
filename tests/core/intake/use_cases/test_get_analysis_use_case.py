from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.errors.analysis_not_found_error import (
    AnalysisNotFoundError,
)
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.use_cases.get_analysis_use_case import GetAnalysisUseCase
from animus.core.shared.domain.structures import Id


def _make_analysis(
    *,
    analysis_id: str = '01ARZ3NDEKTSV4RRFFQ69G5FAV',
    account_id: str = '01BX5ZZKBKACTAV9WEVGEMMVRZ',
) -> Analysis:
    return Analysis.create(
        AnalysisDto(
            id=analysis_id,
            name='Analise inicial',
            folder_id=None,
            account_id=account_id,
            status=AnalysisStatusValue.WAITING_PETITION.value,
            is_archived=False,
            created_at='2026-03-31T10:30:00+00:00',
        )
    )


class TestGetAnalysisUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analisyses_repository_mock = create_autospec(
            AnalisysesRepository,
            instance=True,
        )
        self.use_case = GetAnalysisUseCase(
            analisyses_repository=self.analisyses_repository_mock,
        )

    def test_should_return_analysis_dto_when_analysis_belongs_to_account(self) -> None:
        analysis = _make_analysis()
        self.analisyses_repository_mock.find_by_id.return_value = analysis

        result = self.use_case.execute(
            account_id='01BX5ZZKBKACTAV9WEVGEMMVRZ',
            analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
        )

        self.analisyses_repository_mock.find_by_id.assert_called_once_with(
            Id.create('01ARZ3NDEKTSV4RRFFQ69G5FAV')
        )
        assert result == analysis.dto

    def test_should_raise_analysis_not_found_error_when_analysis_belongs_to_another_account(
        self,
    ) -> None:
        self.analisyses_repository_mock.find_by_id.return_value = _make_analysis(
            account_id='01BX5ZZKBKACTAV9WEVGEMMVS0'
        )

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(
                account_id='01BX5ZZKBKACTAV9WEVGEMMVRZ',
                analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
            )

        self.analisyses_repository_mock.find_by_id.assert_called_once_with(
            Id.create('01ARZ3NDEKTSV4RRFFQ69G5FAV')
        )
