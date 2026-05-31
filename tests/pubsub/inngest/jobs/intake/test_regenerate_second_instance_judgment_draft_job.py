import asyncio
import time
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast

import pytest
from inngest import Inngest, TriggerEvent
from pytest import MonkeyPatch
from sqlalchemy.orm import Session, sessionmaker

from animus.core.intake.domain.errors import (
    DraftRegenerationChosenPrecedentsRequiredError,
)
from animus.core.intake.domain.events import (
    SecondInstanceJudgmentDraftRegenerationTriggeredEvent,
)
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.dtos.second_instance_judgment_draft_dto import (
    SecondInstanceJudgmentDraftDto,
)
from animus.core.intake.domain.structures.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.models.intake import (
    AnalysisModel,
    AnalysisPrecedentModel,
    CaseSummaryModel,
    PrecedentModel,
    SecondInstanceJudgmentDraftModel,
)
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.pipes.ai_pipe import AiPipe
from animus.pubsub.inngest.inngest_broker import InngestBroker
from animus.pubsub.inngest.jobs.intake.regenerate_second_instance_judgment_draft_job import (
    RegenerateSecondInstanceJudgmentDraftJob,
)


def _seed_second_instance_analysis_for_regeneration(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
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
            name='Análise de segunda instância',
            folder_id=None,
            account_id=account_id,
            type=AnalysisType.create_as_second_instance().dto,
            status=SecondInstanceAnalysisStatus.create_as_done().dto,
            is_archived=False,
            created_at=datetime.now(UTC),
        )
    )
    session.add(
        CaseSummaryModel(
            analysis_id=analysis_id,
            case_summary='Resumo objetivo do caso',
            legal_issue='Questão jurídica central',
            central_question='Pergunta central da apelação',
            relevant_laws=['Lei 1'],
            key_facts=['Fato 1'],
            search_terms=['termo 1'],
            requested_relief=['Provimento do recurso'],
            procedural_issues=['Tempestividade'],
        )
    )
    session.add(
        SecondInstanceJudgmentDraftModel(
            analysis_id=analysis_id,
            report='Relatório original',
            merit_analysis='Fundamentação original',
            precedent_adherence_analysis='Aderência original',
            ruling=['Dispositivo original'],
            preliminary_issues='Preliminar original',
            no_applicable_precedent_notice=None,
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
                synthesis=f'Síntese {number}',
                is_manually_added=False,
            )
        )

    session.commit()
    session.close()

    return {
        'analysis_id': analysis_id,
        'account_id': account_id,
        'analysis_type': AnalysisType.create_as_second_instance().dto,
        'chosen_precedent_id': chosen_precedent_id,
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


def _get_judgment_draft(
    sqlalchemy_session_factory: sessionmaker[Session],
    analysis_id: str,
) -> SecondInstanceJudgmentDraftModel | None:
    session = sqlalchemy_session_factory()
    try:
        return session.get(SecondInstanceJudgmentDraftModel, analysis_id)
    finally:
        session.close()


def _wait_until(predicate: Any, *, timeout_seconds: float = 120) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.1)

    raise AssertionError('condition not satisfied before timeout')


class TestRegenerateSecondInstanceJudgmentDraftJob:
    def test_should_register_inngest_function_for_judgment_draft_regeneration_event(
        self,
    ) -> None:
        function = RegenerateSecondInstanceJudgmentDraftJob.handle(
            Inngest(app_id='test')
        )

        assert function._triggers == [  # noqa: SLF001
            TriggerEvent(
                event=SecondInstanceJudgmentDraftRegenerationTriggeredEvent.name,
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
        comments = 'Ajustar fundamentação e dispositivo'
        account_id = Id.create().value
        analysis_type = AnalysisType.create_as_second_instance().dto
        captured_payloads: list[dict[str, str]] = []
        captured_events: list[dict[str, str]] = []

        async def _mark_analysis_as_regenerating_judgment_draft(_payload: Any) -> None:
            return None

        async def _regenerate_and_persist_judgment_draft(
            payload: Any,
        ) -> dict[str, str]:
            captured_payloads.append(
                {
                    'analysis_id': payload.analysis_id,
                    'comments': payload.comments,
                }
            )
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
            RegenerateSecondInstanceJudgmentDraftJob,
            '_mark_analysis_as_regenerating_judgment_draft',
            _mark_analysis_as_regenerating_judgment_draft,
        )
        monkeypatch.setattr(
            RegenerateSecondInstanceJudgmentDraftJob,
            '_regenerate_and_persist_judgment_draft',
            _regenerate_and_persist_judgment_draft,
        )
        monkeypatch.setattr(InngestBroker, 'publish', _publish)

        response = inngest_runtime.post_event(
            name=SecondInstanceJudgmentDraftRegenerationTriggeredEvent.name,
            data={'analysis_id': analysis_id, 'comments': comments},
        )

        assert response.status == 200

        _wait_until(lambda: len(captured_events) == 1)

        assert captured_payloads == [
            {
                'analysis_id': analysis_id,
                'comments': comments,
            }
        ]
        assert captured_events == [
            {
                'name': 'intake/judgment_draft.generation.finished',
                'analysis_id': analysis_id,
                'account_id': account_id,
                'analysis_type': analysis_type,
            }
        ]

    def test_should_regenerate_judgment_draft_and_finish_analysis_when_sync_flow_succeeds(
        self,
        monkeypatch: MonkeyPatch,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_second_instance_analysis_for_regeneration(
            sqlalchemy_session_factory
        )
        captured_workflow_calls: list[dict[str, Any]] = []
        job_module = __import__(
            'animus.pubsub.inngest.jobs.intake.regenerate_second_instance_judgment_draft_job',
            fromlist=['_Payload'],
        )
        payload = job_module._Payload(  # noqa: SLF001
            analysis_id=seeded_data['analysis_id'],
            comments='Ajustar dispositivo e preliminares',
        )

        class _FakeWorkflow:
            def run(
                self,
                *,
                analysis_id: str,
                current_draft: Any,
                case_summary: Any,
                precedents: list[Any],
                comments: str,
            ) -> SecondInstanceJudgmentDraftDto:
                captured_workflow_calls.append(
                    {
                        'analysis_id': analysis_id,
                        'current_report': current_draft.report.value,
                        'case_summary': case_summary.case_summary.value,
                        'precedent_ids': [
                            precedent.precedent.id.value for precedent in precedents
                        ],
                        'chosen_flags': [
                            precedent.is_chosen.is_true for precedent in precedents
                        ],
                        'comments': comments,
                    }
                )
                return SecondInstanceJudgmentDraftDto(
                    analysis_id=analysis_id,
                    report='Relatório revisado',
                    merit_analysis='Fundamentação revisada',
                    precedent_adherence_analysis='Aderência revisada',
                    ruling=['Dispositivo revisado'],
                    preliminary_issues='Preliminar revisada',
                    no_applicable_precedent_notice='Sem observações adicionais',
                )

        monkeypatch.setattr(
            Sqlalchemy,
            'get_session',
            staticmethod(lambda: sqlalchemy_session_factory()),
        )
        monkeypatch.setattr(
            AiPipe,
            'get_regenerate_judgment_draft_workflow',
            staticmethod(lambda: _FakeWorkflow()),
        )

        job_class = cast('Any', RegenerateSecondInstanceJudgmentDraftJob)
        regenerate_and_persist = job_class._regenerate_and_persist_judgment_draft_sync  # noqa: SLF001
        result = regenerate_and_persist(payload)

        persisted_analysis = _get_analysis(
            sqlalchemy_session_factory,
            seeded_data['analysis_id'],
        )
        persisted_judgment_draft = _get_judgment_draft(
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
                'current_report': 'Relatório original',
                'case_summary': 'Resumo objetivo do caso',
                'precedent_ids': [seeded_data['chosen_precedent_id']],
                'chosen_flags': [True],
                'comments': 'Ajustar dispositivo e preliminares',
            }
        ]
        assert (
            persisted_analysis.status
            == SecondInstanceAnalysisStatus.create_as_done().dto
        )
        assert persisted_judgment_draft is not None
        assert persisted_judgment_draft.report == 'Relatório revisado'
        assert persisted_judgment_draft.merit_analysis == 'Fundamentação revisada'
        assert (
            persisted_judgment_draft.precedent_adherence_analysis
            == 'Aderência revisada'
        )
        assert persisted_judgment_draft.ruling == ['Dispositivo revisado']
        assert persisted_judgment_draft.preliminary_issues == 'Preliminar revisada'
        assert (
            persisted_judgment_draft.no_applicable_precedent_notice
            == 'Sem observações adicionais'
        )

    def test_should_raise_error_and_mark_analysis_as_failed_when_no_precedent_is_chosen(
        self,
        monkeypatch: MonkeyPatch,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_second_instance_analysis_for_regeneration(
            sqlalchemy_session_factory,
            with_chosen_precedent=False,
        )
        job_module = __import__(
            'animus.pubsub.inngest.jobs.intake.regenerate_second_instance_judgment_draft_job',
            fromlist=['_Payload'],
        )
        payload = job_module._Payload(  # noqa: SLF001
            analysis_id=seeded_data['analysis_id'],
            comments='Revisar minuta sem precedentes escolhidos',
        )
        context = SimpleNamespace(
            event=SimpleNamespace(
                data={
                    'event': {
                        'data': {
                            'analysis_id': seeded_data['analysis_id'],
                            'comments': 'Revisar minuta sem precedentes escolhidos',
                        }
                    }
                }
            )
        )

        monkeypatch.setattr(
            Sqlalchemy,
            'get_session',
            staticmethod(lambda: sqlalchemy_session_factory()),
        )

        job_class = cast('Any', RegenerateSecondInstanceJudgmentDraftJob)
        regenerate_and_persist = job_class._regenerate_and_persist_judgment_draft_sync  # noqa: SLF001
        handle_failure = job_class._handle_failure  # noqa: SLF001

        with pytest.raises(DraftRegenerationChosenPrecedentsRequiredError):
            regenerate_and_persist(payload)

        asyncio.run(handle_failure(cast('Any', context)))

        persisted_analysis = _get_analysis(
            sqlalchemy_session_factory,
            seeded_data['analysis_id'],
        )
        persisted_judgment_draft = _get_judgment_draft(
            sqlalchemy_session_factory,
            seeded_data['analysis_id'],
        )

        assert (
            persisted_analysis.status
            == SecondInstanceAnalysisStatus.create_as_failed().dto
        )
        assert persisted_judgment_draft is not None
        assert persisted_judgment_draft.report == 'Relatório original'
        assert persisted_judgment_draft.merit_analysis == 'Fundamentação original'
