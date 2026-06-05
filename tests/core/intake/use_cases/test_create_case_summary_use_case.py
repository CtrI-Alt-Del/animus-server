from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.structures.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.intake.domain.errors import AnalysisNotFoundError
from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.dtos.case_summary_dto import CaseSummaryDto
from animus.core.intake.interfaces import (
    AnalysesRepository,
    CaseSummariesRepository,
)
from animus.core.intake.use_cases import CreateCaseSummaryUseCase
from animus.core.shared.domain.structures import Id


def _make_case_summary_dto() -> CaseSummaryDto:
    return CaseSummaryDto(
        case_summary='Resumo do caso',
        legal_issue='Questão juridica',
        central_question='Pergunta central',
        relevant_laws=['Lei 1'],
        key_facts=['Fato 1'],
        search_terms=['termo 1'],
    )


class TestCreateCaseSummaryUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.case_summaries_repository_mock = create_autospec(
            CaseSummariesRepository,
            instance=True,
        )
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository,
            instance=True,
        )
        self.use_case = CreateCaseSummaryUseCase(
            case_summaries_repository=self.case_summaries_repository_mock,
            analyses_repository=self.analyses_repository_mock,
        )

    def test_should_add_case_summary_and_update_case_assessment_status(self) -> None:
        analysis_id = Id.create().value
        dto = _make_case_summary_dto()
        analysis = Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Análise',
                account_id=Id.create().value,
                status=CaseAssessmentAnalysisStatus.create_as_analyzing_case().dto,
                created_at='2026-03-31T10:30:00+00:00',
                type=AnalysisType.create_as_case_assessment().dto,
            )
        )

        self.case_summaries_repository_mock.find_by_analysis_id.return_value = None
        self.analyses_repository_mock.find_by_id.return_value = analysis

        result = self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.case_summaries_repository_mock.add.assert_called_once()
        self.case_summaries_repository_mock.replace.assert_not_called()
        self.analyses_repository_mock.replace.assert_called_once()

        updated_analysis = self.analyses_repository_mock.replace.call_args.args[0]

        assert result == CaseSummary.create(dto).dto
        assert (
            updated_analysis.status
            == CaseAssessmentAnalysisStatus.create_as_case_analyzed()
        )

    def test_should_replace_case_summary_and_update_second_instance_status(
        self,
    ) -> None:
        analysis_id = Id.create().value
        dto = _make_case_summary_dto()
        analysis = Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Análise',
                account_id=Id.create().value,
                status=SecondInstanceAnalysisStatus.create_as_analyzing_case().dto,
                created_at='2026-03-31T10:30:00+00:00',
                type=AnalysisType.create_as_second_instance().dto,
            )
        )

        self.case_summaries_repository_mock.find_by_analysis_id.return_value = object()
        self.analyses_repository_mock.find_by_id.return_value = analysis

        result = self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.case_summaries_repository_mock.add.assert_not_called()
        self.case_summaries_repository_mock.replace.assert_called_once()
        self.analyses_repository_mock.replace.assert_called_once()

        updated_analysis = self.analyses_repository_mock.replace.call_args.args[0]

        assert result == CaseSummary.create(dto).dto
        assert (
            updated_analysis.status
            == SecondInstanceAnalysisStatus.create_as_case_analyzed()
        )

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        dto = _make_case_summary_dto()
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = None
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(analysis_id=analysis_id, dto=dto)

        self.analyses_repository_mock.replace.assert_not_called()
