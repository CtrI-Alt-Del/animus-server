from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.models.intake import AnalysisDocumentModel
from animus.database.sqlalchemy.repositories.intake.sqlalchemy_analyses_repository import (
    SqlalchemyAnalysesRepository,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.fixtures.inngest_fixtures import FakeInngestClient
from tests.rest.controllers.intake.conftest import (
    BuildAuthHeadersFixture,
    CreateAnalysisFixture,
)


def _persist_analysis_document(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    analysis_id: str,
) -> None:
    session = sqlalchemy_session_factory()
    session.add(
        AnalysisDocumentModel(
            analysis_id=analysis_id,
            uploaded_at=datetime(2026, 3, 27, 10, 30, tzinfo=UTC),
            document_file_path='intake/analyses/document.pdf',
            document_name='document.pdf',
        )
    )
    session.commit()
    session.close()


class TestTriggerFirstInstanceCaseSummarizationController:
    def test_should_return_202_publish_event_and_update_analysis_status(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        create_analysis: CreateAnalysisFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(account_id=account.id, status='DOCUMENT_UPLOADED')
        _persist_analysis_document(
            sqlalchemy_session_factory,
            analysis_id=analysis.id,
        )

        response = client.post(
            f'/intake/analyses/{analysis.id}/case-summaries',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 202
        assert len(fake_inngest_client.sent_events) == 1
        assert (
            fake_inngest_client.sent_events[0].name == 'intake/case_summary.requested'
        )
        assert fake_inngest_client.sent_events[0].data['analysis_id'] == analysis.id

        session = sqlalchemy_session_factory()
        persisted_analysis = SqlalchemyAnalysesRepository(session).find_by_id(
            Id.create(analysis.id)
        )
        session.close()

        assert persisted_analysis is not None
        assert persisted_analysis.status.value == 'ANALYZING_CASE'

    def test_should_return_404_when_analysis_document_does_not_exist(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        create_analysis: CreateAnalysisFixture,
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(account_id=account.id, status='DOCUMENT_UPLOADED')

        response = client.post(
            f'/intake/analyses/{analysis.id}/case-summaries',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 404
        assert len(fake_inngest_client.sent_events) == 0
