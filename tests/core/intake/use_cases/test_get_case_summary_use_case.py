from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.errors import CaseSummaryUnavailableError
from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.dtos.case_summary_dto import CaseSummaryDto
from animus.core.intake.interfaces import CaseSummariesRepository
from animus.core.intake.use_cases.get_case_summary_use_case import (
    GetCaseSummaryUseCase,
)
from animus.core.shared.domain.structures import Id


class TestGetCaseSummaryUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.case_summaries_repository_mock = create_autospec(
            CaseSummariesRepository,
            instance=True,
        )
        self.use_case = GetCaseSummaryUseCase(
            case_summaries_repository=self.case_summaries_repository_mock,
        )

    def test_should_return_case_summary_dto_when_summary_exists(self) -> None:
        analysis_id = Id.create().value
        case_summary = CaseSummary.create(
            CaseSummaryDto(
                case_summary='Resumo do caso',
                legal_issue='Questao juridica',
                central_question='Pergunta central',
                relevant_laws=['Lei 1'],
                key_facts=['Fato 1'],
                search_terms=['termo 1'],
            )
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = (
            case_summary
        )

        result = self.use_case.execute(analysis_id=analysis_id)

        self.case_summaries_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id=Id.create(analysis_id),
        )
        assert result == case_summary.dto

    def test_should_raise_case_summary_unavailable_error_when_summary_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(CaseSummaryUnavailableError):
            self.use_case.execute(analysis_id=analysis_id)

        self.case_summaries_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id=Id.create(analysis_id),
        )
