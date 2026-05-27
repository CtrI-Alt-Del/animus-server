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
    CaseAssessmentCaseSummarizationTriggeredEvent,
)
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.structures.dtos.case_summary_dto import CaseSummaryDto
from animus.core.intake.use_cases.create_case_summary_use_case import (
    CreateCaseSummaryUseCase,
)
from animus.core.shared.domain.structures import Id, Text
from animus.database.sqlalchemy.models.intake import (
    AnalysisDocumentModel,
    AnalysisModel,
    CaseSummaryModel,
)
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.pipes.ai_pipe import AiPipe
from animus.pubsub.inngest.inngest_broker import InngestBroker
from animus.pubsub.inngest.jobs.intake.summarize_case_assessment_case_job import (
    SummarizeCaseAssessmentCaseJob,
)


def _seed_case_assessment_analysis_with_document(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> dict[str, str]:
    analysis_id = Id.create().value
    account_id = Id.create().value

    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Análise case assessment',
            account_id=account_id,
            folder_id=None,
            type=AnalysisType.create_as_case_assessment().dto,
            status=CaseAssessmentAnalysisStatus.create_as_analyzing_case().dto,
            is_archived=False,
            created_at=datetime.now(UTC),
        )
    )
    session.add(
        AnalysisDocumentModel(
            analysis_id=analysis_id,
            uploaded_at=datetime.now(UTC),
            document_file_path='documents/analysis.pdf',
            document_name='analysis.pdf',
        )
    )
    session.commit()
    session.close()

    return {
        'analysis_id': analysis_id,
        'account_id': account_id,
        'analysis_type': AnalysisType.create_as_case_assessment().dto,
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


def _get_case_summary(
    sqlalchemy_session_factory: sessionmaker[Session],
    analysis_id: str,
) -> CaseSummaryModel | None:
    session = sqlalchemy_session_factory()
    try:
        return session.get(CaseSummaryModel, analysis_id)
    finally:
        session.close()


def _wait_until(predicate: Any, *, timeout_seconds: float = 30) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.1)

    raise AssertionError('condition not satisfied before timeout')


class TestSummarizeCaseAssessmentCaseJob:
    def test_should_register_inngest_function_for_case_assessment_summary_requested_event(
        self,
    ) -> None:
        function = SummarizeCaseAssessmentCaseJob.handle(Inngest(app_id='test'))

        assert function._triggers == [  # noqa: SLF001
            TriggerEvent(event=CaseAssessmentCaseSummarizationTriggeredEvent.name)
        ]

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
        analysis_type = AnalysisType.create_as_case_assessment().dto
        captured_payloads: list[str] = []
        captured_events: list[dict[str, str]] = []

        async def _summarize_case(payload: Any) -> dict[str, str]:
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
            SummarizeCaseAssessmentCaseJob,
            '_summarize_case',
            _summarize_case,
        )
        monkeypatch.setattr(InngestBroker, 'publish', _publish)

        response = inngest_runtime.post_event(
            name=CaseAssessmentCaseSummarizationTriggeredEvent.name,
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
                'analysis_type': analysis_type,
            }
        ]

    def test_should_persist_case_summary_and_update_analysis_status_when_sync_flow_succeeds(
        self,
        monkeypatch: MonkeyPatch,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_case_assessment_analysis_with_document(
            sqlalchemy_session_factory
        )
        captured_calls: list[dict[str, Any]] = []
        job_module = __import__(
            'animus.pubsub.inngest.jobs.intake.summarize_case_assessment_case_job',
            fromlist=['_Payload'],
        )
        payload = job_module._Payload(analysis_id=seeded_data['analysis_id'])  # noqa: SLF001

        class _FakeWorkflow:
            def __init__(self, repositories: dict[str, Any]) -> None:
                self._repositories = repositories

            def run(
                self, *, analysis_id: str, document_content: Text
            ) -> CaseSummaryDto:
                captured_calls.append(
                    {
                        'analysis_id': analysis_id,
                        'document_content': document_content.value,
                    }
                )
                dto = CaseSummaryDto(
                    case_summary='Resumo estruturado do caso',
                    legal_issue='Questão jurídica principal',
                    central_question='Pergunta central',
                    relevant_laws=['Lei 1'],
                    key_facts=['Fato 1'],
                    search_terms=['termo 1'],
                    requested_relief=['Pedido 1'],
                    procedural_issues=['Questão processual 1'],
                )
                return CreateCaseSummaryUseCase(
                    case_summaries_repository=self._repositories[
                        'case_summaries_repository'
                    ],
                    analysis_documents_repository=self._repositories[
                        'analysis_documents_repository'
                    ],
                    analyses_repository=self._repositories['analyses_repository'],
                ).execute(
                    analysis_id=analysis_id,
                    dto=dto,
                )

        def _get_workflow(**repositories: Any) -> _FakeWorkflow:
            return _FakeWorkflow(repositories)

        def _execute(_self: Any, *, file_path: Any) -> Text:
            assert file_path.value == 'documents/analysis.pdf'
            return Text.create('Conteúdo do documento para sumarização')

        monkeypatch.setattr(
            Sqlalchemy,
            'get_session',
            staticmethod(lambda: sqlalchemy_session_factory()),
        )
        monkeypatch.setattr(
            'animus.core.storage.use_cases.get_document_content_use_case.GetDocumentContentUseCase.execute',
            _execute,
        )
        monkeypatch.setattr(
            AiPipe,
            'get_summarize_case_assessment_case_workflow',
            staticmethod(_get_workflow),
        )

        job_class = cast('Any', SummarizeCaseAssessmentCaseJob)
        summarize_case = job_class._summarize_case_sync  # noqa: SLF001
        result = summarize_case(payload)

        persisted_analysis = _get_analysis(
            sqlalchemy_session_factory,
            seeded_data['analysis_id'],
        )
        persisted_case_summary = _get_case_summary(
            sqlalchemy_session_factory,
            seeded_data['analysis_id'],
        )

        assert result == seeded_data
        assert captured_calls == [
            {
                'analysis_id': seeded_data['analysis_id'],
                'document_content': 'Conteúdo do documento para sumarização',
            }
        ]
        assert (
            persisted_analysis.status
            == CaseAssessmentAnalysisStatus.create_as_case_analyzed().dto
        )
        assert persisted_case_summary is not None
        assert persisted_case_summary.case_summary == 'Resumo estruturado do caso'
        assert persisted_case_summary.legal_issue == 'Questão jurídica principal'
        assert persisted_case_summary.central_question == 'Pergunta central'
        assert persisted_case_summary.requested_relief == ['Pedido 1']
        assert persisted_case_summary.procedural_issues == ['Questão processual 1']

    def test_should_mark_analysis_as_failed_when_failure_handler_receives_event_payload(
        self,
        monkeypatch: MonkeyPatch,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        seeded_data = _seed_case_assessment_analysis_with_document(
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

        job_class = cast('Any', SummarizeCaseAssessmentCaseJob)
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
