import time
from typing import Any

import pytest
from pytest import MonkeyPatch
from sqlalchemy.orm import Session, sessionmaker

from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.intake.domain.events import (
    CaseSummaryFinishedEvent,
    SecondInstanceCaseSummarizationTriggeredEvent,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.models.intake.analysis_model import AnalysisModel
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.pubsub.inngest.inngest_broker import InngestBroker
from animus.pubsub.inngest.jobs.intake.summarize_second_instance_case_job import (
    SummarizeSecondInstanceCaseJob,
)


def _seed_second_instance_analysis(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> dict[str, str]:
    analysis_id = Id.create().value
    account_id = Id.create().value

    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Análise de teste',
            account_id=account_id,
            folder_id=None,
            type=AnalysisType.create_as_second_instance().dto,
            status=SecondInstanceAnalysisStatus.create_as_extracting_court_document_pieces().dto,
            is_archived=False,
        )
    )
    session.commit()
    session.close()

    return {
        'analysis_id': analysis_id,
        'account_id': account_id,
        'analysis_type': AnalysisType.create_as_second_instance().dto,
    }


def _wait_until(predicate: Any, *, timeout_seconds: float = 60) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.1)

    raise AssertionError('condition not satisfied before timeout')


class TestSummarizeSecondInstanceCaseJob:
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
        analysis_type = AnalysisType.create_as_second_instance().dto
        captured_payloads: list[str] = []
        captured_events: list[dict[str, str]] = []

        async def _extract_and_summarize_case(payload: Any) -> dict[str, str]:
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
            SummarizeSecondInstanceCaseJob,
            '_extract_and_summarize_case',
            _extract_and_summarize_case,
        )
        monkeypatch.setattr(InngestBroker, 'publish', _publish)

        response = inngest_runtime.post_event(
            name=SecondInstanceCaseSummarizationTriggeredEvent.name,
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
                'analysis_type': analysis_type,
            }
        ]

    def test_should_mark_analysis_as_court_document_pieces_not_found_when_extraction_is_not_found(
        self,
        monkeypatch: MonkeyPatch,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_second_instance_analysis(sqlalchemy_session_factory)
        job_module = __import__(
            'animus.pubsub.inngest.jobs.intake.summarize_second_instance_case_job',
            fromlist=['_Payload'],
        )
        payload_factory = getattr(job_module, '_Payload')  # noqa: B009
        mark_court_document_pieces_as_not_found_sync = getattr(  # noqa: B009
            SummarizeSecondInstanceCaseJob,
            '_mark_court_document_pieces_as_not_found_sync',
        )
        monkeypatch.setattr(
            Sqlalchemy,
            'get_session',
            staticmethod(lambda: sqlalchemy_session_factory()),
        )

        mark_court_document_pieces_as_not_found_sync(
            payload_factory(analysis_id=seeded_data['analysis_id'])
        )

        session = sqlalchemy_session_factory()
        persisted_analysis = session.get(AnalysisModel, seeded_data['analysis_id'])
        session.close()

        assert persisted_analysis is not None
        assert (
            persisted_analysis.status
            == SecondInstanceAnalysisStatus.create_as_court_document_pieces_not_found().dto
        )
