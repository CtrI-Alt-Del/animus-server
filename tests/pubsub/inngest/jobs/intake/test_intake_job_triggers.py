import time
from typing import Any
from datetime import UTC, datetime
import pytest
from pytest import MonkeyPatch
from animus.core.shared.domain.structures import Id
from animus.core.intake.domain.events import PetitionSummaryRequestedEvent, AnalysisPrecedentsSearchRequestedEvent, PetitionSummaryFinishedEvent, PrecedentsSearchFinishedEvent
from animus.pubsub.inngest.jobs.intake.summarize_petition_job import SummarizePetitionJob
from animus.pubsub.inngest.jobs.intake.search_analysis_precedents_job import SearchAnalysisPrecedentsJob
from animus.database.sqlalchemy.models.intake.analysis_model import AnalysisModel
from animus.database.sqlalchemy.models.intake.petition_model import PetitionModel
from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from sqlalchemy.orm import Session, sessionmaker
from animus.pubsub.inngest.inngest_broker import InngestBroker


def _seed_data(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> dict[str, str]:
    analysis_id = Id.create().value
    petition_id = Id.create().value
    account_id = Id.create().value

    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Analise de teste',
            account_id=account_id,
            folder_id=None,
            status=AnalysisStatusValue.WAITING_PETITION.value,
            is_archived=False,
        )
    )
    session.add(
        PetitionModel(
            id=petition_id,
            analysis_id=analysis_id,
            uploaded_at=datetime.now(UTC),
            document_file_path='petitions/test.pdf',
            document_name='test.pdf',
        )
    )
    session.commit()
    session.close()

    return {
        'analysis_id': analysis_id,
        'petition_id': petition_id,
    }


class TestIntakeJobTriggers:
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.legacy is deprecated:DeprecationWarning'
    )
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.server\.WebSocketServerProtocol is deprecated:DeprecationWarning'
    )
    def test_summarize_petition_job_should_publish_finished_event(
        self,
        monkeypatch: MonkeyPatch,
        inngest_runtime: Any,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_data(sqlalchemy_session_factory)
        published_events: list[str] = []

        async def _summarize_petition(payload: Any) -> str:
            return seeded_data['analysis_id']

        def _publish(_self: InngestBroker, event: Any) -> None:
            published_events.append(event.name)

        monkeypatch.setattr(SummarizePetitionJob, '_summarize_petition', _summarize_petition)
        monkeypatch.setattr(InngestBroker, 'publish', _publish)

        response = inngest_runtime.post_event(
            name=PetitionSummaryRequestedEvent.name,
            data={'petition_id': seeded_data['petition_id']},
        )

        assert response.status == 200

        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if PetitionSummaryFinishedEvent.name in published_events:
                break
            time.sleep(0.1)
        else:
            msg = 'PetitionSummaryFinishedEvent not published'
            raise AssertionError(msg)

    @pytest.mark.filterwarnings(
        r'ignore:websockets\.legacy is deprecated:DeprecationWarning'
    )
    @pytest.mark.filterwarnings(
        r'ignore:websockets\.server\.WebSocketServerProtocol is deprecated:DeprecationWarning'
    )
    def test_search_analysis_precedents_job_should_publish_finished_event(
        self,
        monkeypatch: MonkeyPatch,
        inngest_runtime: Any,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_data(sqlalchemy_session_factory)
        published_events: list[str] = []

        async def _search_precedents(payload: Any) -> list[dict[str, Any]]:
            return []
        
        async def _mark_analysis_as_analyzing_similarity(payload: Any) -> None:
            pass

        async def _synthesize_analysis_precedents(payload: Any, data: Any) -> None:
            pass

        def _publish(_self: InngestBroker, event: Any) -> None:
            published_events.append(event.name)

        monkeypatch.setattr(SearchAnalysisPrecedentsJob, '_search_precedents', _search_precedents)
        monkeypatch.setattr(SearchAnalysisPrecedentsJob, '_mark_analysis_as_analyzing_similarity', _mark_analysis_as_analyzing_similarity)
        monkeypatch.setattr(SearchAnalysisPrecedentsJob, '_synthesize_analysis_precedents', _synthesize_analysis_precedents)
        monkeypatch.setattr(InngestBroker, 'publish', _publish)

        response = inngest_runtime.post_event(
            name=AnalysisPrecedentsSearchRequestedEvent.name,
            data={
                'analysis_id': seeded_data['analysis_id'],
                'courts': [],
                'precedent_kinds': [],
                'limit': 5
            },
        )

        assert response.status == 200

        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if PrecedentsSearchFinishedEvent.name in published_events:
                break
            time.sleep(0.1)
        else:
            msg = 'PrecedentsSearchFinishedEvent not published'
            raise AssertionError(msg)
