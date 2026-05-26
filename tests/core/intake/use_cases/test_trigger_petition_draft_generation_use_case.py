from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    AnalysisPrecedentsUnavailableError,
    CaseSummaryUnavailableError,
    ChosenAnalysisPrecedentsRequiredError,
    InconsistentAnalysisTypeError,
)
from animus.core.intake.domain.entities.dtos import PrecedentDto
from animus.core.intake.domain.events import PetitionDraftGenerationTriggeredEvent
from animus.core.intake.domain.structures import AnalysisPrecedent, CaseSummary
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.dtos import (
    AnalysisPrecedentDto,
    CaseSummaryDto,
    PrecedentIdentifierDto,
)
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalysesRepository,
    CaseSummariesRepository,
)
from animus.core.intake.use_cases import TriggerPetitionDraftGenerationUseCase
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker
from animus.core.shared.responses import ListResponse


class TestTriggerPetitionDraftGenerationUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository,
            instance=True,
        )
        self.case_summaries_repository_mock = create_autospec(
            CaseSummariesRepository,
            instance=True,
        )
        self.analysis_precedents_repository_mock = create_autospec(
            AnalysisPrecedentsRepository,
            instance=True,
        )
        self.broker_mock = create_autospec(Broker, instance=True)
        self.use_case = TriggerPetitionDraftGenerationUseCase(
            analyses_repository=self.analyses_repository_mock,
            case_summaries_repository=self.case_summaries_repository_mock,
            analysis_precedents_repository=self.analysis_precedents_repository_mock,
            broker=self.broker_mock,
        )

    def test_should_publish_event_when_there_is_at_least_one_chosen_precedent(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis_id_entity = Id.create(analysis_id)
        analysis = self._create_analysis(
            analysis_id,
            AnalysisType.create_as_case_assessment().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = (
            CaseSummary.create(self._create_case_summary_dto())
        )
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.return_value = ListResponse(
            items=[
                self._create_analysis_precedent(
                    analysis_id,
                    101,
                    is_chosen=True,
                ),
                self._create_analysis_precedent(
                    analysis_id,
                    102,
                    is_chosen=False,
                ),
            ]
        )

        self.use_case.execute(analysis_id)

        self.analyses_repository_mock.find_by_id.assert_called_once_with(
            analysis_id_entity,
        )
        self.case_summaries_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id_entity,
        )
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.assert_called_once_with(
            analysis_id_entity,
        )
        self.broker_mock.publish.assert_called_once()

        event = self.broker_mock.publish.call_args.args[0]
        assert isinstance(event, PetitionDraftGenerationTriggeredEvent)
        assert event.payload.analysis_id == analysis_id

    def test_should_raise_when_no_precedent_is_chosen(self) -> None:
        analysis_id = Id.create().value
        analysis = self._create_analysis(
            analysis_id,
            AnalysisType.create_as_case_assessment().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = (
            CaseSummary.create(self._create_case_summary_dto())
        )
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.return_value = ListResponse(
            items=[
                self._create_analysis_precedent(
                    analysis_id,
                    101,
                    is_chosen=False,
                ),
            ]
        )

        with pytest.raises(ChosenAnalysisPrecedentsRequiredError):
            self.use_case.execute(analysis_id)

        self.broker_mock.publish.assert_not_called()

    def test_should_raise_when_analysis_has_no_precedents(self) -> None:
        analysis_id = Id.create().value
        analysis = self._create_analysis(
            analysis_id,
            AnalysisType.create_as_case_assessment().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = (
            CaseSummary.create(self._create_case_summary_dto())
        )
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.return_value = ListResponse(
            items=[]
        )

        with pytest.raises(AnalysisPrecedentsUnavailableError):
            self.use_case.execute(analysis_id)

        self.broker_mock.publish.assert_not_called()

    def test_should_raise_when_analysis_does_not_exist(self) -> None:
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(Id.create().value)

        self.case_summaries_repository_mock.find_by_analysis_id.assert_not_called()
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_when_analysis_is_not_case_assessment(self) -> None:
        analysis_id = Id.create().value
        analysis = self._create_analysis(
            analysis_id,
            AnalysisType.create_as_second_instance().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis

        with pytest.raises(InconsistentAnalysisTypeError):
            self.use_case.execute(analysis_id)

        self.case_summaries_repository_mock.find_by_analysis_id.assert_not_called()
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_when_case_summary_does_not_exist(self) -> None:
        analysis_id = Id.create().value
        analysis = self._create_analysis(
            analysis_id,
            AnalysisType.create_as_case_assessment().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(CaseSummaryUnavailableError):
            self.use_case.execute(analysis_id)

        self.analysis_precedents_repository_mock.find_many_by_analysis_id.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    @staticmethod
    def _create_analysis(analysis_id: str, analysis_type: str) -> Analysis:
        return Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Analise',
                folder_id=None,
                account_id=Id.create().value,
                type=analysis_type,
                status='DONE',
                is_archived=False,
                created_at='2026-03-31T10:30:00+00:00',
            )
        )

    @staticmethod
    def _create_case_summary_dto() -> CaseSummaryDto:
        return CaseSummaryDto(
            case_summary='Resumo',
            legal_issue='Questao',
            central_question='Pergunta',
            relevant_laws=['Lei 1'],
            key_facts=['Fato 1'],
            search_terms=['Termo 1'],
        )

    @staticmethod
    def _create_analysis_precedent(
        analysis_id: str,
        number: int,
        is_chosen: bool,
    ) -> AnalysisPrecedent:
        return AnalysisPrecedent.create(
            AnalysisPrecedentDto(
                analysis_id=analysis_id,
                precedent=PrecedentDto(
                    id=Id.create().value,
                    identifier=PrecedentIdentifierDto(
                        court='STF',
                        kind='RG',
                        number=number,
                    ),
                    status='vigente',
                    enunciation='Enunciado',
                    thesis='Tese',
                    last_updated_in_pangea_at='2026-03-31T10:30:00+00:00',
                ),
                is_chosen=is_chosen,
                similarity_score=85.0,
                synthesis='Sintese',
                applicability_level=2 if is_chosen else 1,
            )
        )
