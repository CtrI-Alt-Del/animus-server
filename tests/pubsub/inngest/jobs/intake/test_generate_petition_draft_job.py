import asyncio
import time
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast

import pytest
from inngest import Inngest, TriggerEvent
from pytest import MonkeyPatch
from sqlalchemy.orm import Session, sessionmaker

from animus.core.intake.domain.events import (
    PetitionDraftGenerationTriggeredEvent,
)
from animus.core.intake.domain.errors import ChosenAnalysisPrecedentsRequiredError
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.structures.dtos.petition_draft_dto import (
    PetitionDraftDto,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.models.intake import (
    AnalysisModel,
    AnalysisPrecedentModel,
    CaseSummaryModel,
    PetitionDraftModel,
    PrecedentModel,
)
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.pipes.ai_pipe import AiPipe
from animus.pubsub.inngest.inngest_broker import InngestBroker
from animus.pubsub.inngest.jobs.intake.generate_petition_draft_job import (
    GeneratePetitionDraftJob,
)


def _seed_case_assessment_analysis(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    with_case_summary: bool = True,
    with_chosen_precedent: bool = True,
) -> dict[str, str]:
    analysis_id = Id.create().value
    account_id = Id.create().value
    chosen_precedent_id = Id.create().value
    unchosen_precedent_id = Id.create().value

    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Análise case assessment',
            folder_id=None,
            account_id=account_id,
            type=AnalysisType.create_as_case_assessment().dto,
            status=CaseAssessmentAnalysisStatus.create_as_case_analyzed().dto,
            is_archived=False,
            created_at=datetime.now(UTC),
        )
    )

    if with_case_summary:
        session.add(
            CaseSummaryModel(
                analysis_id=analysis_id,
                case_summary='Resumo objetivo do caso',
                legal_issue='Questao juridica central',
                central_question='Pergunta principal',
                relevant_laws=['Lei 1'],
                key_facts=['Fato 1'],
                search_terms=['termo 1'],
                type_of_action='Ação de obrigação de fazer',
                secondary_legal_issues=['Questão acessória'],
                alternative_questions=['Pergunta alternativa'],
                jurisdiction_issue='Competência estadual',
                standing_issue='Legitimidade ativa presente',
                requested_relief=['Concessão do pedido'],
                procedural_issues=['Sem preliminares'],
                excluded_or_accessory_topics=['Danos morais'],
            )
        )

    for precedent_id, number, is_chosen in [
        (chosen_precedent_id, 101, with_chosen_precedent),
        (unchosen_precedent_id, 102, False),
    ]:
        session.add(
            PrecedentModel(
                id=precedent_id,
                court='STJ',
                kind='RG',
                number=number,
                status='vigente',
                enunciation=f'Enunciado {number}',
                thesis=f'Tese {number}',
                last_updated_in_pangea_at=datetime.now(UTC),
            )
        )
        session.add(
            AnalysisPrecedentModel(
                analysis_id=analysis_id,
                precedent_id=precedent_id,
                is_chosen=is_chosen,
                similarity_score=float(200 - number),
                thesis_similarity_score=0.9,
                enunciation_similarity_score=0.8,
                total_search_hits=12,
                similarity_rank=number - 100,
                final_rank=number - 100,
                applicability_level=2 if is_chosen else 1,
                synthesis=f'Sintese {number}',
                is_manually_added=False,
            )
        )

    session.commit()
    session.close()

    return {
        'analysis_id': analysis_id,
        'account_id': account_id,
        'analysis_type': AnalysisType.create_as_case_assessment().dto,
        'chosen_precedent_id': chosen_precedent_id,
        'unchosen_precedent_id': unchosen_precedent_id,
    }


def _get_analysis(
    sqlalchemy_session_factory: sessionmaker[Session],
    analysis_id: str,
) -> AnalysisModel:
    session = sqlalchemy_session_factory()
    try:
        model = session.get(AnalysisModel, analysis_id)
        assert model is not None
        return model
    finally:
        session.close()


def _get_petition_draft(
    sqlalchemy_session_factory: sessionmaker[Session],
    analysis_id: str,
) -> PetitionDraftModel | None:
    session = sqlalchemy_session_factory()
    try:
        return session.get(PetitionDraftModel, analysis_id)
    finally:
        session.close()


def _wait_until(predicate: Any, *, timeout_seconds: float = 120) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.1)

    raise AssertionError('condition not satisfied before timeout')


class TestGeneratePetitionDraftJob:
    def test_should_register_inngest_function_for_petition_draft_generation_event(
        self,
    ) -> None:
        function = GeneratePetitionDraftJob.handle(Inngest(app_id='test'))

        assert function._triggers == [  # noqa: SLF001
            TriggerEvent(
                event=PetitionDraftGenerationTriggeredEvent.name,
            )
        ]

    @pytest.mark.filterwarnings(
        r'ignore:websockets\.legacy is deprecated:DeprecationWarning'
    )
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.server\.WebSocketServerProtocol is deprecated:DeprecationWarning'
    )
    def test_should_process_event_and_publish_finished_event_when_runtime_flow_succeeds(
        self,
        monkeypatch: MonkeyPatch,
        inngest_runtime: Any,
    ) -> None:
        analysis_id = Id.create().value
        account_id = Id.create().value
        analysis_type = AnalysisType.create_as_case_assessment().dto
        captured_payloads: list[str] = []
        captured_events: list[dict[str, str]] = []

        async def _mark_analysis_as_generating_petition_draft(_payload: Any) -> None:
            return None

        async def _generate_and_persist_petition_draft(payload: Any) -> dict[str, str]:
            captured_payloads.append(payload.analysis_id)
            return {
                'analysis_id': analysis_id,
                'account_id': account_id,
                'analysis_type': analysis_type,
            }

        def _publish(_self: InngestBroker, event: Any) -> None:
            captured_events.append(
                {
                    'name': event.name,
                    'analysis_id': event.payload_data['analysis_id'],
                    'account_id': event.payload_data['account_id'],
                    'analysis_type': event.payload_data['analysis_type'],
                }
            )

        monkeypatch.setattr(
            GeneratePetitionDraftJob,
            '_mark_analysis_as_generating_petition_draft',
            _mark_analysis_as_generating_petition_draft,
        )
        monkeypatch.setattr(
            GeneratePetitionDraftJob,
            '_generate_and_persist_petition_draft',
            _generate_and_persist_petition_draft,
        )
        monkeypatch.setattr(InngestBroker, 'publish', _publish)

        response = inngest_runtime.post_event(
            name=PetitionDraftGenerationTriggeredEvent.name,
            data={'analysis_id': analysis_id},
        )

        assert response.status == 200

        _wait_until(lambda: len(captured_events) == 1)

        assert captured_payloads == [analysis_id]
        assert captured_events == [
            {
                'name': 'intake/petition_draft.generation.finished',
                'analysis_id': analysis_id,
                'account_id': account_id,
                'analysis_type': analysis_type,
            }
        ]

    def test_should_persist_petition_draft_and_finish_analysis_when_sync_flow_succeeds(
        self,
        monkeypatch: MonkeyPatch,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_case_assessment_analysis(sqlalchemy_session_factory)
        captured_workflow_calls: list[dict[str, Any]] = []
        job_module = __import__(
            'animus.pubsub.inngest.jobs.intake.generate_petition_draft_job',
            fromlist=['_Payload'],
        )
        payload = job_module._Payload(analysis_id=seeded_data['analysis_id'])  # noqa: SLF001

        class _FakeWorkflow:
            def run(
                self,
                *,
                analysis_id: str,
                case_summary: Any,
                precedents: list[Any],
            ) -> PetitionDraftDto:
                captured_workflow_calls.append(
                    {
                        'analysis_id': analysis_id,
                        'case_summary': case_summary.case_summary.value,
                        'precedent_ids': [
                            precedent.precedent.id.value for precedent in precedents
                        ],
                        'chosen_flags': [
                            precedent.is_chosen.is_true for precedent in precedents
                        ],
                    }
                )
                return PetitionDraftDto(
                    analysis_id=analysis_id,
                    structured_facts='Fatos estruturados',
                    legal_grounds='Fundamentos juridicos',
                    central_thesis='Tese central',
                    requests=['Pedido 1', 'Pedido 2'],
                    precedent_citations=['Citacao 1'],
                )

        monkeypatch.setattr(
            Sqlalchemy,
            'get_session',
            staticmethod(lambda: sqlalchemy_session_factory()),
        )
        monkeypatch.setattr(
            AiPipe,
            'get_generate_petition_draft_workflow',
            staticmethod(lambda: _FakeWorkflow()),
        )

        job_class = cast('Any', GeneratePetitionDraftJob)
        generate_and_persist = job_class._generate_and_persist_petition_draft_sync  # noqa: SLF001
        result = generate_and_persist(payload)

        persisted_analysis = _get_analysis(
            sqlalchemy_session_factory,
            seeded_data['analysis_id'],
        )
        persisted_petition_draft = _get_petition_draft(
            sqlalchemy_session_factory,
            seeded_data['analysis_id'],
        )

        assert result == {
            'analysis_id': seeded_data['analysis_id'],
            'account_id': seeded_data['account_id'],
            'analysis_type': seeded_data['analysis_type'],
        }
        assert captured_workflow_calls == [
            {
                'analysis_id': seeded_data['analysis_id'],
                'case_summary': 'Resumo objetivo do caso',
                'precedent_ids': [seeded_data['chosen_precedent_id']],
                'chosen_flags': [True],
            }
        ]
        assert (
            persisted_analysis.status
            == CaseAssessmentAnalysisStatus.create_as_done().dto
        )
        assert persisted_petition_draft is not None
        assert persisted_petition_draft.structured_facts == 'Fatos estruturados'
        assert persisted_petition_draft.legal_grounds == 'Fundamentos juridicos'
        assert persisted_petition_draft.central_thesis == 'Tese central'
        assert persisted_petition_draft.requests == ['Pedido 1', 'Pedido 2']
        assert persisted_petition_draft.precedent_citations == ['Citacao 1']

    def test_should_return_none_and_not_persist_petition_draft_when_case_summary_does_not_exist(
        self,
        monkeypatch: MonkeyPatch,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_case_assessment_analysis(
            sqlalchemy_session_factory,
            with_case_summary=False,
        )
        job_module = __import__(
            'animus.pubsub.inngest.jobs.intake.generate_petition_draft_job',
            fromlist=['_Payload'],
        )
        payload = job_module._Payload(analysis_id=seeded_data['analysis_id'])  # noqa: SLF001

        monkeypatch.setattr(
            Sqlalchemy,
            'get_session',
            staticmethod(lambda: sqlalchemy_session_factory()),
        )

        job_class = cast('Any', GeneratePetitionDraftJob)
        generate_and_persist = job_class._generate_and_persist_petition_draft_sync  # noqa: SLF001
        result = generate_and_persist(payload)

        persisted_analysis = _get_analysis(
            sqlalchemy_session_factory,
            seeded_data['analysis_id'],
        )

        assert result is None
        assert (
            persisted_analysis.status
            == CaseAssessmentAnalysisStatus.create_as_case_analyzed().dto
        )
        assert (
            _get_petition_draft(sqlalchemy_session_factory, seeded_data['analysis_id'])
            is None
        )

    def test_should_raise_error_when_no_precedent_is_chosen_and_mark_analysis_as_failed(
        self,
        monkeypatch: MonkeyPatch,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_case_assessment_analysis(
            sqlalchemy_session_factory,
            with_chosen_precedent=False,
        )
        job_module = __import__(
            'animus.pubsub.inngest.jobs.intake.generate_petition_draft_job',
            fromlist=['_Payload'],
        )
        payload = job_module._Payload(analysis_id=seeded_data['analysis_id'])  # noqa: SLF001
        context = SimpleNamespace(
            event=SimpleNamespace(
                data={
                    'event': {
                        'data': {'analysis_id': seeded_data['analysis_id']},
                    }
                }
            )
        )

        monkeypatch.setattr(
            Sqlalchemy,
            'get_session',
            staticmethod(lambda: sqlalchemy_session_factory()),
        )

        job_class = cast('Any', GeneratePetitionDraftJob)
        generate_and_persist = job_class._generate_and_persist_petition_draft_sync  # noqa: SLF001
        handle_failure = job_class._handle_failure  # noqa: SLF001

        with pytest.raises(ChosenAnalysisPrecedentsRequiredError):
            generate_and_persist(payload)

        asyncio.run(handle_failure(cast('Any', context)))

        persisted_analysis = _get_analysis(
            sqlalchemy_session_factory,
            seeded_data['analysis_id'],
        )

        assert (
            persisted_analysis.status
            == CaseAssessmentAnalysisStatus.create_as_failed().dto
        )
        assert (
            _get_petition_draft(sqlalchemy_session_factory, seeded_data['analysis_id'])
            is None
        )

    def test_should_mark_analysis_as_failed_when_failure_handler_receives_event_payload(
        self,
        monkeypatch: MonkeyPatch,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_case_assessment_analysis(sqlalchemy_session_factory)
        context = SimpleNamespace(
            event=SimpleNamespace(
                data={
                    'event': {
                        'data': {'analysis_id': seeded_data['analysis_id']},
                    }
                }
            )
        )

        monkeypatch.setattr(
            Sqlalchemy,
            'get_session',
            staticmethod(lambda: sqlalchemy_session_factory()),
        )

        job_class = cast('Any', GeneratePetitionDraftJob)
        handle_failure = job_class._handle_failure  # noqa: SLF001
        asyncio.run(handle_failure(cast('Any', context)))

        persisted_analysis = _get_analysis(
            sqlalchemy_session_factory,
            seeded_data['analysis_id'],
        )

        assert (
            persisted_analysis.status
            == CaseAssessmentAnalysisStatus.create_as_failed().dto
        )
        assert (
            _get_petition_draft(sqlalchemy_session_factory, seeded_data['analysis_id'])
            is None
        )
