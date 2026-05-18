import time
from typing import Any

import pytest
from pytest import MonkeyPatch
from sqlalchemy.orm import Session, sessionmaker

from animus.core.intake.domain.entities.analysis_type import AnalysisType
from animus.core.intake.domain.entities.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.intake.domain.events import (
    CaseSummaryFinishedEvent,
    PetitionExtractionRequestedEvent,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.models.intake.analysis_model import AnalysisModel
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.pubsub.inngest.inngest_broker import InngestBroker
from animus.pubsub.inngest.jobs.intake.extract_petition_job import ExtractPetitionJob


def _seed_second_instance_analysis(
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
            type=AnalysisType.SECOND_INSTANCE.value,
            status=SecondInstanceAnalysisStatus.EXTRACTING_PETITION.value,
            is_archived=False,
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


class TestExtractPetitionJob:
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
        analysis_id = Id.create().value
        account_id = Id.create().value
        captured_payloads: list[str] = []
        captured_events: list[dict[str, str]] = []

        async def _extract_and_summarize(payload: Any) -> dict[str, str]:
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

        monkeypatch.setattr(
            ExtractPetitionJob,
            '_extract_and_summarize',
            _extract_and_summarize,
        )
        monkeypatch.setattr(InngestBroker, 'publish', _publish)

        response = inngest_runtime.post_event(
            name=PetitionExtractionRequestedEvent.name,
            data={'analysis_id': analysis_id},
        )

        assert response.status == 200

        _wait_until(lambda: len(captured_events) == 1)

        assert captured_payloads == [analysis_id]
        assert captured_events == [
            {
                'name': CaseSummaryFinishedEvent.name,
                'analysis_id': analysis_id,
                'account_id': account_id,
            }
        ]

    def test_should_mark_analysis_as_petition_not_found_when_extraction_is_not_found(
        self,
        monkeypatch: MonkeyPatch,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_second_instance_analysis(sqlalchemy_session_factory)
        job_module = __import__(
            'animus.pubsub.inngest.jobs.intake.extract_petition_job',
            fromlist=['_Payload'],
        )
        payload_factory = getattr(job_module, '_Payload')  # noqa: B009
        mark_petition_as_not_found_sync = getattr(  # noqa: B009
            ExtractPetitionJob,
            '_mark_petition_as_not_found_sync',
        )
        monkeypatch.setattr(
            Sqlalchemy,
            'get_session',
            staticmethod(lambda: sqlalchemy_session_factory()),
        )

        mark_petition_as_not_found_sync(
            payload_factory(analysis_id=seeded_data['analysis_id'])
        )

        session = sqlalchemy_session_factory()
        persisted_analysis = session.get(AnalysisModel, seeded_data['analysis_id'])
        session.close()

        assert persisted_analysis is not None
        assert (
            persisted_analysis.status
            == SecondInstanceAnalysisStatus.PETITION_NOT_FOUND.value
        )
