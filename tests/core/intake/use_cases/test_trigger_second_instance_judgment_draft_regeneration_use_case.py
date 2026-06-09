from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.entities.dtos.precedent_dto import PrecedentDto
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    DraftRegenerationCaseSummaryUnavailableError,
    DraftRegenerationChosenPrecedentsRequiredError,
    DraftRegenerationCommentsRequiredError,
    SecondInstanceAnalysisRequiredError,
    SecondInstanceJudgmentDraftRegenerationUnavailableError,
)
from animus.core.intake.domain.events import (
    SecondInstanceJudgmentDraftRegenerationTriggeredEvent,
)
from animus.core.intake.domain.structures import AnalysisPrecedent, CaseSummary
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.dtos import (
    AnalysisPrecedentDto,
    CaseSummaryDto,
    PrecedentIdentifierDto,
    SecondInstanceJudgmentDraftDto,
)
from animus.core.intake.domain.structures.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.intake.domain.structures.second_instance_judgment_draft import (
    SecondInstanceJudgmentDraft,
)
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalysesRepository,
    CaseSummariesRepository,
    SecondInstanceJudgmentDraftsRepository,
)
from animus.core.intake.use_cases import (
    TriggerSecondInstanceJudgmentDraftRegenerationUseCase,
)
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker
from animus.core.shared.responses import ListResponse


class TestTriggerSecondInstanceJudgmentDraftRegenerationUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository,
            instance=True,
        )
        self.judgment_drafts_repository_mock = create_autospec(
            SecondInstanceJudgmentDraftsRepository,
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
        self.use_case = TriggerSecondInstanceJudgmentDraftRegenerationUseCase(
            analyses_repository=self.analyses_repository_mock,
            judgment_drafts_repository=self.judgment_drafts_repository_mock,
            case_summaries_repository=self.case_summaries_repository_mock,
            analysis_precedents_repository=self.analysis_precedents_repository_mock,
            broker=self.broker_mock,
        )

    def test_should_publish_event_with_trimmed_comments_when_preconditions_are_satisfied(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_second_instance().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.judgment_drafts_repository_mock.find_by_analysis_id.return_value = (
            self._create_judgment_draft(analysis_id)
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = (
            CaseSummary.create(self._create_case_summary_dto())
        )
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.return_value = ListResponse(
            items=[self._create_analysis_precedent(analysis_id, 101, is_chosen=True)]
        )

        self.use_case.execute(
            analysis_id=analysis_id, comments='  Ajustar fundamentação  '
        )

        self.analyses_repository_mock.find_by_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        self.judgment_drafts_repository_mock.find_by_analysis_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        self.case_summaries_repository_mock.find_by_analysis_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        self.analyses_repository_mock.replace.assert_called_once_with(analysis)
        self.broker_mock.publish.assert_called_once()
        event = self.broker_mock.publish.call_args.args[0]
        assert isinstance(event, SecondInstanceJudgmentDraftRegenerationTriggeredEvent)
        assert event.payload.analysis_id == analysis_id
        assert event.payload.comments == 'Ajustar fundamentação'
        assert (
            analysis.status
            == SecondInstanceAnalysisStatus.create_as_generating_judgment_draft()
        )

    def test_should_raise_comments_required_error_when_comments_are_blank(self) -> None:
        analysis_id = Id.create().value

        with pytest.raises(DraftRegenerationCommentsRequiredError):
            self.use_case.execute(analysis_id=analysis_id, comments='   ')

        self.analyses_repository_mock.find_by_id.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(analysis_id=analysis_id, comments='Revisar voto')

        self.judgment_drafts_repository_mock.find_by_analysis_id.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_second_instance_analysis_required_error_when_analysis_is_not_second_instance(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_case_assessment().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis

        with pytest.raises(SecondInstanceAnalysisRequiredError):
            self.use_case.execute(analysis_id=analysis_id, comments='Revisar voto')

        self.judgment_drafts_repository_mock.find_by_analysis_id.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_judgment_draft_regeneration_unavailable_error_when_draft_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_second_instance().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.judgment_drafts_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(SecondInstanceJudgmentDraftRegenerationUnavailableError):
            self.use_case.execute(analysis_id=analysis_id, comments='Revisar voto')

        self.case_summaries_repository_mock.find_by_analysis_id.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_case_summary_unavailable_error_when_case_summary_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_second_instance().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.judgment_drafts_repository_mock.find_by_analysis_id.return_value = (
            self._create_judgment_draft(analysis_id)
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(DraftRegenerationCaseSummaryUnavailableError):
            self.use_case.execute(analysis_id=analysis_id, comments='Revisar voto')

        self.analysis_precedents_repository_mock.find_many_by_analysis_id.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_chosen_precedents_required_error_when_analysis_has_no_precedents(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_second_instance().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.judgment_drafts_repository_mock.find_by_analysis_id.return_value = (
            self._create_judgment_draft(analysis_id)
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = (
            CaseSummary.create(self._create_case_summary_dto())
        )
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.return_value = ListResponse(
            items=[]
        )

        with pytest.raises(DraftRegenerationChosenPrecedentsRequiredError):
            self.use_case.execute(analysis_id=analysis_id, comments='Revisar voto')

        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_chosen_precedents_required_error_when_no_precedent_is_chosen(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis = self._create_analysis(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.create_as_second_instance().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.judgment_drafts_repository_mock.find_by_analysis_id.return_value = (
            self._create_judgment_draft(analysis_id)
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = (
            CaseSummary.create(self._create_case_summary_dto())
        )
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.return_value = ListResponse(
            items=[self._create_analysis_precedent(analysis_id, 101, is_chosen=False)]
        )

        with pytest.raises(DraftRegenerationChosenPrecedentsRequiredError):
            self.use_case.execute(analysis_id=analysis_id, comments='Revisar voto')

        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    @staticmethod
    def _create_analysis(analysis_id: str, analysis_type: str) -> Analysis:
        return Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Análise',
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
            legal_issue='Questão',
            central_question='Pergunta',
            relevant_laws=['Lei 1'],
            key_facts=['Fato 1'],
            search_terms=['Termo 1'],
        )

    @staticmethod
    def _create_judgment_draft(analysis_id: str) -> SecondInstanceJudgmentDraft:
        return SecondInstanceJudgmentDraft.create(
            SecondInstanceJudgmentDraftDto(
                analysis_id=analysis_id,
                report='Relatório',
                merit_analysis='Fundamentação',
                precedent_adherence_analysis='Aderência',
                ruling=['Dispositivo 1'],
                preliminary_issues='Preliminar',
                no_applicable_precedent_notice='Aviso',
            )
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
                        court='STJ',
                        kind='RG',
                        number=number,
                    ),
                    status='vigente',
                    enunciation='Enunciado',
                    thesis='Tese',
                    last_updated_in_pangea_at='2026-03-31T10:30:00+00:00',
                ),
                is_chosen=is_chosen,
                similarity_score=91.0,
                synthesis='Síntese',
                applicability_level=2 if is_chosen else 1,
            )
        )
