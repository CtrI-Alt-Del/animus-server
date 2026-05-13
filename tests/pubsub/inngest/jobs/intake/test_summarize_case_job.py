import time
from datetime import UTC, datetime
from typing import Any

import pytest
from pytest import MonkeyPatch
from sqlalchemy.orm import Session, sessionmaker

from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.models.intake.analysis_model import AnalysisModel
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.pubsub.inngest.inngest_broker import InngestBroker
from animus.pubsub.inngest.jobs.intake.summarize_case_job import SummarizeCaseJob


def _seed_analysis(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> dict[str, str]:
    analysis_id = Id.create().value
    account_id = Id.create().value

    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Analise de teste',
            account_id=account_id,
            folder_id=None,
            type='FIRST_INSTANCE',
            status='ANALYZING_CASE',
            is_archived=False,
            created_at=datetime.now(UTC),
        )
    )
    session.commit()
    session.close()

    return {'analysis_id': analysis_id, 'account_id': account_id}


def _wait_until(predicate: Any, *, timeout_seconds: float = 30) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.1)

    raise AssertionError('condition not satisfied before timeout')


class TestSummarizeCaseJob:
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.legacy is deprecated:DeprecationWarning'
    )
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.server\.WebSocketServerProtocol is deprecated:DeprecationWarning'
    )
    def test_should_process_event_and_publish_finished_event(
        self,
        monkeypatch: MonkeyPatch,
        inngest_runtime: Any,
    ) -> None:
        captured_payloads: list[str] = []
        captured_events: list[dict[str, str]] = []
        analysis_id = Id.create().value
        account_id = Id.create().value

        async def _summarize_case(payload: Any) -> dict[str, str]:
            captured_payloads.append(payload.analysis_id)
            return {'analysis_id': analysis_id, 'account_id': account_id}

        def _publish(_self: InngestBroker, event: Any) -> None:
            captured_events.append(
                {
                    'name': event.name,
                    'analysis_id': event.payload_data['analysis_id'],
                    'account_id': event.payload_data['account_id'],
                }
            )

        monkeypatch.setattr(SummarizeCaseJob, '_summarize_case', _summarize_case)
        monkeypatch.setattr(InngestBroker, 'publish', _publish)

        response = inngest_runtime.post_event(
            name='intake/case_summary.requested',
            data={'analysis_id': analysis_id},
        )

        assert response.status == 200

        _wait_until(lambda: len(captured_events) == 1)

        assert captured_payloads == [analysis_id]
        assert captured_events == [
            {
                'name': 'intake/case_summary.finished',
                'analysis_id': analysis_id,
                'account_id': account_id,
            }
        ]

    def test_should_mark_analysis_as_failed_when_failure_handler_runs(
        self,
        monkeypatch: MonkeyPatch,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_analysis(sqlalchemy_session_factory)
        job_module = __import__(
            'animus.pubsub.inngest.jobs.intake.summarize_case_job',
            fromlist=['_Payload'],
        )
        payload_factory = getattr(job_module, '_Payload')  # noqa: B009
        mark_analysis_as_failed_sync = getattr(  # noqa: B009
            SummarizeCaseJob,
            '_mark_analysis_as_failed_sync',
        )
        monkeypatch.setattr(
            Sqlalchemy,
            'get_session',
            staticmethod(lambda: sqlalchemy_session_factory()),
        )

        mark_analysis_as_failed_sync(
            payload_factory(analysis_id=seeded_data['analysis_id'])
        )

        session = sqlalchemy_session_factory()
        persisted_analysis = session.get(AnalysisModel, seeded_data['analysis_id'])
        session.close()

        assert persisted_analysis is not None
        assert persisted_analysis.status == 'FAILED'
