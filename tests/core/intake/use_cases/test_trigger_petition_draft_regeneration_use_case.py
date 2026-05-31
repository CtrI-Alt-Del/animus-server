from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.entities.dtos import PrecedentDto
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    DraftRegenerationCaseSummaryUnavailableError,
    DraftRegenerationChosenPrecedentsRequiredError,
    DraftRegenerationCommentsRequiredError,
    InconsistentAnalysisTypeError,
    PetitionDraftRegenerationUnavailableError,
)
from animus.core.intake.domain.events import PetitionDraftRegenerationTriggeredEvent
from animus.core.intake.domain.structures import (
    AnalysisPrecedent,
    CaseSummary,
    PetitionDraft,
)
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.dtos import (
    AnalysisPrecedentDto,
    CaseSummaryDto,
    PetitionDraftDto,
    PrecedentIdentifierDto,
)
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalysesRepository,
    CaseSummariesRepository,
    PetitionDraftsRepository,
)
from animus.core.intake.use_cases import TriggerPetitionDraftRegenerationUseCase
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker
from animus.core.shared.responses import ListResponse


class TestTriggerPetitionDraftRegenerationUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository,
            instance=True,
        )
        self.petition_drafts_repository_mock = create_autospec(
            PetitionDraftsRepository,
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
        self.use_case = TriggerPetitionDraftRegenerationUseCase(
            analyses_repository=self.analyses_repository_mock,
            petition_drafts_repository=self.petition_drafts_repository_mock,
            case_summaries_repository=self.case_summaries_repository_mock,
            analysis_precedents_repository=self.analysis_precedents_repository_mock,
            broker=self.broker_mock,
        )

    def test_should_publish_event_with_normalized_comments_when_preconditions_are_met(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis_id_entity = Id.create(analysis_id)
        analysis = self._create_analysis(
            analysis_id,
            AnalysisType.create_as_case_assessment().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.petition_drafts_repository_mock.find_by_analysis_id.return_value = (
            self._create_petition_draft(analysis_id)
        )
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

        self.use_case.execute(
            analysis_id=analysis_id, comments='  Ajuste os pedidos finais  '
        )

        self.analyses_repository_mock.find_by_id.assert_called_once_with(
            analysis_id_entity,
        )
        self.petition_drafts_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id_entity,
        )
        self.case_summaries_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id_entity,
        )
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.assert_called_once_with(
            analysis_id_entity,
        )
        self.analyses_repository_mock.replace.assert_called_once_with(analysis)
        self.broker_mock.publish.assert_called_once()

        event = self.broker_mock.publish.call_args.args[0]
        assert isinstance(event, PetitionDraftRegenerationTriggeredEvent)
        assert event.payload.analysis_id == analysis_id
        assert event.payload.comments == 'Ajuste os pedidos finais'
        assert (
            analysis.status
            == CaseAssessmentAnalysisStatus.create_as_generating_petition_draft()
        )

    def test_should_raise_comments_required_error_when_comments_are_blank(
        self,
    ) -> None:
        with pytest.raises(DraftRegenerationCommentsRequiredError):
            self.use_case.execute(analysis_id=Id.create().value, comments='   ')

        self.analyses_repository_mock.find_by_id.assert_not_called()
        self.petition_drafts_repository_mock.find_by_analysis_id.assert_not_called()
        self.case_summaries_repository_mock.find_by_analysis_id.assert_not_called()
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis_id_entity = Id.create(analysis_id)
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(analysis_id=analysis_id, comments='Comentario valido')

        self.analyses_repository_mock.find_by_id.assert_called_once_with(
            analysis_id_entity,
        )
        self.petition_drafts_repository_mock.find_by_analysis_id.assert_not_called()
        self.case_summaries_repository_mock.find_by_analysis_id.assert_not_called()
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_when_analysis_is_not_case_assessment(self) -> None:
        analysis_id = Id.create().value
        analysis = self._create_analysis(
            analysis_id,
            AnalysisType.create_as_second_instance().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis

        with pytest.raises(InconsistentAnalysisTypeError):
            self.use_case.execute(analysis_id=analysis_id, comments='Comentario valido')

        self.petition_drafts_repository_mock.find_by_analysis_id.assert_not_called()
        self.case_summaries_repository_mock.find_by_analysis_id.assert_not_called()
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_when_petition_draft_is_unavailable(self) -> None:
        analysis_id = Id.create().value
        analysis_id_entity = Id.create(analysis_id)
        analysis = self._create_analysis(
            analysis_id,
            AnalysisType.create_as_case_assessment().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.petition_drafts_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(PetitionDraftRegenerationUnavailableError):
            self.use_case.execute(analysis_id=analysis_id, comments='Comentario valido')

        self.petition_drafts_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id_entity,
        )
        self.case_summaries_repository_mock.find_by_analysis_id.assert_not_called()
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_when_case_summary_is_unavailable(self) -> None:
        analysis_id = Id.create().value
        analysis_id_entity = Id.create(analysis_id)
        analysis = self._create_analysis(
            analysis_id,
            AnalysisType.create_as_case_assessment().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.petition_drafts_repository_mock.find_by_analysis_id.return_value = (
            self._create_petition_draft(analysis_id)
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(DraftRegenerationCaseSummaryUnavailableError):
            self.use_case.execute(analysis_id=analysis_id, comments='Comentario valido')

        self.petition_drafts_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id_entity,
        )
        self.case_summaries_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id_entity,
        )
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_when_analysis_has_no_precedents(self) -> None:
        analysis_id = Id.create().value
        analysis = self._create_analysis(
            analysis_id,
            AnalysisType.create_as_case_assessment().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.petition_drafts_repository_mock.find_by_analysis_id.return_value = (
            self._create_petition_draft(analysis_id)
        )
        self.case_summaries_repository_mock.find_by_analysis_id.return_value = (
            CaseSummary.create(self._create_case_summary_dto())
        )
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.return_value = ListResponse(
            items=[]
        )

        with pytest.raises(DraftRegenerationChosenPrecedentsRequiredError):
            self.use_case.execute(analysis_id=analysis_id, comments='Comentario valido')

        self.broker_mock.publish.assert_not_called()

    def test_should_raise_when_no_precedent_is_chosen(self) -> None:
        analysis_id = Id.create().value
        analysis = self._create_analysis(
            analysis_id,
            AnalysisType.create_as_case_assessment().dto,
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.petition_drafts_repository_mock.find_by_analysis_id.return_value = (
            self._create_petition_draft(analysis_id)
        )
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

        with pytest.raises(DraftRegenerationChosenPrecedentsRequiredError):
            self.use_case.execute(analysis_id=analysis_id, comments='Comentario valido')

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
    def _create_petition_draft(analysis_id: str) -> PetitionDraft:
        return PetitionDraft.create(
            PetitionDraftDto(
                analysis_id=analysis_id,
                structured_facts='Fatos estruturados',
                legal_grounds='Fundamentos juridicos',
                central_thesis='Tese central',
                requests=['Pedido 1'],
                precedent_citations=['Citacao 1'],
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
