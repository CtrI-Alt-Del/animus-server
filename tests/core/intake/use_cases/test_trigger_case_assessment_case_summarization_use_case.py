from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    CaseAssessmentBriefingNotFoundError,
    InconsistentAnalysisTypeError,
)
from animus.core.intake.domain.events import (
    CaseAssessmentCaseSummarizationTriggeredEvent,
)
from animus.core.intake.domain.structures.case_assessment_briefing import (
    CaseAssessmentBriefing,
)
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.structures.dtos.case_assessment_briefing_dto import (
    CaseAssessmentBriefingDto,
)
from animus.core.intake.interfaces import (
    AnalysesRepository,
    CaseAssessmentBriefingsRepository,
)
from animus.core.intake.use_cases import (
    TriggerCaseAssessmentCaseSummarizationUseCase,
)
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker


class TestTriggerCaseAssessmentCaseSummarizationUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.case_assessment_briefings_repository_mock = create_autospec(
            CaseAssessmentBriefingsRepository,
            instance=True,
        )
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository,
            instance=True,
        )
        self.broker_mock = create_autospec(Broker, instance=True)
        self.use_case = TriggerCaseAssessmentCaseSummarizationUseCase(
            case_assessment_briefings_repository=self.case_assessment_briefings_repository_mock,
            analyses_repository=self.analyses_repository_mock,
            broker=self.broker_mock,
        )

    def test_should_publish_event_and_update_analysis_status_when_analysis_is_case_assessment(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis_id_entity = Id.create(analysis_id)
        briefing = self._create_briefing(analysis_id=analysis_id)
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_case_assessment().dto,
            status=CaseAssessmentAnalysisStatus.create_as_briefing_submitted().dto,
        )
        self.case_assessment_briefings_repository_mock.find_by_analysis_id.return_value = briefing
        self.analyses_repository_mock.find_by_id.return_value = analysis

        self.use_case.execute(analysis_id=analysis_id)

        self.case_assessment_briefings_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id=analysis_id_entity,
        )
        self.analyses_repository_mock.find_by_id.assert_called_once_with(
            analysis_id_entity
        )
        self.analyses_repository_mock.replace.assert_called_once()
        self.broker_mock.publish.assert_called_once()

        updated_analysis = self.analyses_repository_mock.replace.call_args.args[0]
        published_event = self.broker_mock.publish.call_args.args[0]

        assert (
            updated_analysis.status
            == CaseAssessmentAnalysisStatus.create_as_analyzing_case()
        )
        assert isinstance(
            published_event, CaseAssessmentCaseSummarizationTriggeredEvent
        )
        assert published_event.payload.analysis_id == analysis_id

    def test_should_raise_case_assessment_briefing_not_found_error_when_briefing_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        self.case_assessment_briefings_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(CaseAssessmentBriefingNotFoundError):
            self.use_case.execute(analysis_id=analysis_id)

        self.analyses_repository_mock.find_by_id.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        self.case_assessment_briefings_repository_mock.find_by_analysis_id.return_value = self._create_briefing(
            analysis_id=analysis_id
        )
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(analysis_id=analysis_id)

        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_inconsistent_analysis_type_error_when_analysis_is_not_case_assessment(
        self,
    ) -> None:
        analysis_id = Id.create().value
        self.case_assessment_briefings_repository_mock.find_by_analysis_id.return_value = self._create_briefing(
            analysis_id=analysis_id
        )
        self.analyses_repository_mock.find_by_id.return_value = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_first_instance().dto,
            status='DOCUMENT_UPLOADED',
        )

        with pytest.raises(
            InconsistentAnalysisTypeError,
            match=r'Tipo de análise incoerente|Tipo de analise incoerente',
        ):
            self.use_case.execute(analysis_id=analysis_id)

        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    @staticmethod
    def _create_briefing(analysis_id: str) -> CaseAssessmentBriefing:
        return CaseAssessmentBriefing.create(
            CaseAssessmentBriefingDto(
                analysis_id=analysis_id,
                legal_area='CIVIL',
                court_jurisdiction='TJSP',
                main_claims='Pedido principal',
                intended_thesis='Tese principal',
            )
        )

    @staticmethod
    def _create_analysis(
        analysis_id: str,
        analysis_type: str,
        status: str,
    ) -> Analysis:
        return Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Análise',
                account_id=Id.create().value,
                status=status,
                created_at='2026-03-31T10:30:00+00:00',
                type=analysis_type,
            )
        )
