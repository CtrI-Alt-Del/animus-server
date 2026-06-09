import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from typing import cast

from inngest import Inngest, TriggerEvent
import pytest
from pytest import MonkeyPatch
from sqlalchemy.orm import Session, sessionmaker

from animus.core.intake.domain.errors import SecondInstanceDecisionNotFoundError
from animus.core.intake.domain.events import (
    SecondInstanceJudgmentDraftGenerationTriggeredEvent,
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
    SecondInstanceDecisionModel,
    SecondInstanceJudgmentDraftModel,
)
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.pipes.ai_pipe import AiPipe
from animus.pubsub.inngest.jobs.intake.generate_second_instance_judgment_draft_job import (
    GenerateSecondInstanceJudgmentDraftJob,
)


def _seed_second_instance_analysis_with_summary_and_precedents(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> dict[str, str]:
    analysis_id = Id.create().value
    chosen_precedent_id = Id.create().value
    unchosen_precedent_id = Id.create().value

    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Análise de segunda instancia',
            folder_id=None,
            account_id=Id.create().value,
            type=AnalysisType.create_as_second_instance().dto,
            status=SecondInstanceAnalysisStatus.create_as_case_analyzed().dto,
            is_archived=False,
            created_at=datetime.now(UTC),
        )
    )
    session.add(
        CaseSummaryModel(
            analysis_id=analysis_id,
            case_summary='Resumo objetivo do caso',
            legal_issue='Questão juridica central',
            central_question='Pergunta central da apelação',
            relevant_laws=['Lei 1'],
            key_facts=['Fato 1'],
            search_terms=['termo 1'],
            requested_relief=['Provimento do recurso'],
            procedural_issues=['Tempestividade'],
        )
    )
    session.add(
        SecondInstanceDecisionModel(
            analysis_id=analysis_id,
            description='Dar provimento ao recurso com reforma parcial da sentença.',
        )
    )

    for precedent_id, number, is_chosen in [
        (chosen_precedent_id, 101, True),
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
                final_rank=number - 100,
                applicability_level=2 if is_chosen else 1,
                synthesis=f'Sintese {number}',
            )
        )

    session.commit()
    session.close()

    return {
        'analysis_id': analysis_id,
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


def _get_judgment_draft(
    sqlalchemy_session_factory: sessionmaker[Session],
    analysis_id: str,
) -> SecondInstanceJudgmentDraftModel | None:
    session = sqlalchemy_session_factory()
    try:
        return session.get(SecondInstanceJudgmentDraftModel, analysis_id)
    finally:
        session.close()


class TestGenerateSecondInstanceJudgmentDraftJob:
    def test_should_register_inngest_function_for_judgment_draft_generation_event(
        self,
    ) -> None:
        function = GenerateSecondInstanceJudgmentDraftJob.handle(Inngest(app_id='test'))

        assert function._triggers == [  # noqa: SLF001
            TriggerEvent(
                event=SecondInstanceJudgmentDraftGenerationTriggeredEvent.name,
            )
        ]

    def test_should_persist_judgment_draft_and_finish_analysis_when_sync_flow_succeeds(
        self,
        monkeypatch: MonkeyPatch,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_second_instance_analysis_with_summary_and_precedents(
            sqlalchemy_session_factory
        )
        captured_calls: list[dict[str, Any]] = []
        job_module = __import__(
            'animus.pubsub.inngest.jobs.intake.generate_second_instance_judgment_draft_job',
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
                second_instance_decision: Any,
            ) -> SecondInstanceJudgmentDraftDto:
                captured_calls.append(
                    {
                        'analysis_id': analysis_id,
                        'case_summary': case_summary.case_summary.value,
                        'second_instance_decision': (
                            second_instance_decision.description.value
                        ),
                        'precedent_ids': [
                            precedent.precedent.id.value for precedent in precedents
                        ],
                        'chosen_flags': [
                            precedent.is_chosen.is_true for precedent in precedents
                        ],
                    }
                )
                return SecondInstanceJudgmentDraftDto(
                    analysis_id=analysis_id,
                    report='Relatório',
                    merit_analysis='Fundamentação',
                    precedent_adherence_analysis='Aderência',
                    ruling=['Dispositivo'],
                )

        monkeypatch.setattr(
            Sqlalchemy,
            'get_session',
            staticmethod(lambda: sqlalchemy_session_factory()),
        )
        monkeypatch.setattr(
            AiPipe,
            'get_generate_judgment_draft_workflow',
            staticmethod(lambda: _FakeWorkflow()),
        )

        job_class = cast('Any', GenerateSecondInstanceJudgmentDraftJob)
        generate_and_persist = job_class._generate_and_persist_judgment_draft_sync  # noqa: SLF001
        generate_and_persist(payload)

        persisted_analysis = _get_analysis(
            sqlalchemy_session_factory,
            seeded_data['analysis_id'],
        )
        persisted_judgment_draft = _get_judgment_draft(
            sqlalchemy_session_factory,
            seeded_data['analysis_id'],
        )

        assert captured_calls == [
            {
                'analysis_id': seeded_data['analysis_id'],
                'case_summary': 'Resumo objetivo do caso',
                'second_instance_decision': 'Dar provimento ao recurso com reforma parcial da sentença.',
                'precedent_ids': [seeded_data['chosen_precedent_id']],
                'chosen_flags': [True],
            }
        ]
        assert (
            persisted_analysis.status
            == SecondInstanceAnalysisStatus.create_as_done().dto
        )
        assert persisted_judgment_draft is not None
        assert persisted_judgment_draft.report == 'Relatório'
        assert persisted_judgment_draft.merit_analysis == 'Fundamentação'
        assert persisted_judgment_draft.precedent_adherence_analysis == 'Aderência'
        assert persisted_judgment_draft.ruling == ['Dispositivo']

    def test_should_mark_analysis_as_failed_when_failure_handler_receives_event_payload(
        self,
        monkeypatch: MonkeyPatch,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_second_instance_analysis_with_summary_and_precedents(
            sqlalchemy_session_factory
        )
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

        job_class = cast('Any', GenerateSecondInstanceJudgmentDraftJob)
        handle_failure = job_class._handle_failure  # noqa: SLF001
        asyncio.run(handle_failure(cast('Any', context)))

        persisted_analysis = _get_analysis(
            sqlalchemy_session_factory,
            seeded_data['analysis_id'],
        )

        assert (
            persisted_analysis.status
            == SecondInstanceAnalysisStatus.create_as_failed().dto
        )
        assert (
            _get_judgment_draft(sqlalchemy_session_factory, seeded_data['analysis_id'])
            is None
        )

    def test_should_raise_when_second_instance_decision_does_not_exist(
        self,
        monkeypatch: MonkeyPatch,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_second_instance_analysis_with_summary_and_precedents(
            sqlalchemy_session_factory
        )

        with sqlalchemy_session_factory() as session:
            decision = session.get(
                SecondInstanceDecisionModel, seeded_data['analysis_id']
            )
            assert decision is not None
            session.delete(decision)
            session.commit()

        job_module = __import__(
            'animus.pubsub.inngest.jobs.intake.generate_second_instance_judgment_draft_job',
            fromlist=['_Payload'],
        )
        payload = job_module._Payload(analysis_id=seeded_data['analysis_id'])  # noqa: SLF001

        monkeypatch.setattr(
            Sqlalchemy,
            'get_session',
            staticmethod(lambda: sqlalchemy_session_factory()),
        )

        job_class = cast('Any', GenerateSecondInstanceJudgmentDraftJob)
        generate_and_persist = job_class._generate_and_persist_judgment_draft_sync  # noqa: SLF001

        with pytest.raises(SecondInstanceDecisionNotFoundError):
            generate_and_persist(payload)
