from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    SecondInstanceDecisionNotFoundError,
)
from animus.core.intake.domain.events import AnalysisPrecedentsSearchTriggeredEvent
from animus.core.intake.domain.structures import CaseSummary, SecondInstanceDecision
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.dtos import (
    AnalysisPrecedentsSearchFiltersDto,
    CaseSummaryDto,
    SecondInstanceDecisionDto,
)
from animus.core.intake.interfaces import (
    AnalysesRepository,
    CaseSummariesRepository,
    SecondInstanceDecisionsRepository,
)
from animus.core.intake.use_cases import RequestAnalysisPrecedentsSearchUseCase
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker


class TestRequestAnalysisPrecedentsSearchUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository,
            instance=True,
        )
        self.second_instance_decisions_repository_mock = create_autospec(
            SecondInstanceDecisionsRepository,
            instance=True,
        )
        self.case_summaries_repository_mock = create_autospec(
            CaseSummariesRepository,
            instance=True,
        )
        self.broker_mock = create_autospec(Broker, instance=True)
        self.use_case = RequestAnalysisPrecedentsSearchUseCase(
            analyses_repository=self.analyses_repository_mock,
            second_instance_decisions_repository=self.second_instance_decisions_repository_mock,
            case_summaries_repository=self.case_summaries_repository_mock,
            broker=self.broker_mock,
        )

    def test_should_publish_event_for_first_instance_without_decision(self) -> None:
        analysis_id = Id.create().value
        self.analyses_repository_mock.find_by_id.return_value = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_first_instance().dto,
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = (
            CaseSummary.create(self._create_case_summary_dto())
        )

        self.use_case.execute(
            analysis_id=analysis_id,
            dto=AnalysisPrecedentsSearchFiltersDto(
                courts=['STJ'],
                precedent_kinds=['RG'],
                limit=5,
            ),
        )

        self.second_instance_decisions_repository_mock.find_by_analysis_id.assert_not_called()
        self.broker_mock.publish.assert_called_once()
        event = self.broker_mock.publish.call_args.args[0]
        assert isinstance(event, AnalysisPrecedentsSearchTriggeredEvent)
        assert event.payload.analysis_id == analysis_id

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(
                analysis_id=Id.create().value,
                dto=AnalysisPrecedentsSearchFiltersDto(),
            )

    def test_should_raise_decision_not_found_error_for_second_instance_without_decision(
        self,
    ) -> None:
        analysis_id = Id.create().value
        self.analyses_repository_mock.find_by_id.return_value = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_second_instance().dto,
        )
        self.second_instance_decisions_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(SecondInstanceDecisionNotFoundError):
            self.use_case.execute(
                analysis_id=analysis_id,
                dto=AnalysisPrecedentsSearchFiltersDto(),
            )

        self.case_summaries_repository_mock.find_by_analysis_id.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_publish_event_for_second_instance_with_decision(self) -> None:
        analysis_id = Id.create().value
        self.analyses_repository_mock.find_by_id.return_value = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_second_instance().dto,
        )
        self.second_instance_decisions_repository_mock.find_by_analysis_id.return_value = SecondInstanceDecision.create(
            SecondInstanceDecisionDto(
                analysis_id=analysis_id,
                description='Dar parcial provimento',
            )
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = (
            CaseSummary.create(self._create_case_summary_dto())
        )

        self.use_case.execute(
            analysis_id=analysis_id,
            dto=AnalysisPrecedentsSearchFiltersDto(limit=3),
        )

        self.broker_mock.publish.assert_called_once()

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

    @staticmethod
    def _create_case_summary_dto() -> CaseSummaryDto:
        return CaseSummaryDto(
            case_summary='Resumo',
            legal_issue='Questão jurídica',
            central_question='Pergunta',
            relevant_laws=['Lei 1'],
            key_facts=['Fato 1'],
            search_terms=['Termo 1'],
        )
