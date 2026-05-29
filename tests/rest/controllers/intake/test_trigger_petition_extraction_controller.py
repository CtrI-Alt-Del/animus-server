from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
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


class TestSecondInstanceCaseSummarizationController:
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
        analysis = create_analysis(
            account_id=account.id,
            analysis_type=AnalysisType.create_as_second_instance().dto,
            status=SecondInstanceAnalysisStatus.create_as_document_uploaded().dto,
        )
        _persist_analysis_document(
            sqlalchemy_session_factory,
            analysis_id=analysis.id,
        )

        response = client.post(
            f'/intake/analyses/{analysis.id}/petition-extraction',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 202
        assert len(fake_inngest_client.sent_events) == 1
        assert (
            fake_inngest_client.sent_events[0].name
            == 'intake/petition.extraction.triggered'
        )
        assert fake_inngest_client.sent_events[0].data['analysis_id'] == analysis.id

        session = sqlalchemy_session_factory()
        persisted_analysis = SqlalchemyAnalysesRepository(session).find_by_id(
            Id.create(analysis.id)
        )
        session.close()

        assert persisted_analysis is not None
        assert (
            persisted_analysis.status.value
            == SecondInstanceAnalysisStatus.create_as_analyzing_case().dto
        )

    def test_should_return_403_when_analysis_belongs_to_another_account(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        create_analysis: CreateAnalysisFixture,
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        authenticated_account = create_account(is_verified=True, is_active=True)
        owner_account = create_account(
            email='owner@example.com',
            is_verified=True,
            is_active=True,
        )
        analysis = create_analysis(
            account_id=owner_account.id,
            analysis_type=AnalysisType.create_as_second_instance().dto,
            status=SecondInstanceAnalysisStatus.create_as_document_uploaded().dto,
        )

        response = client.post(
            f'/intake/analyses/{analysis.id}/petition-extraction',
            headers=build_auth_headers(authenticated_account.id),
        )

        assert response.status_code == 403
        assert len(fake_inngest_client.sent_events) == 0

    def test_should_return_404_when_analysis_document_does_not_exist(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        create_analysis: CreateAnalysisFixture,
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(
            account_id=account.id,
            analysis_type=AnalysisType.create_as_second_instance().dto,
            status=SecondInstanceAnalysisStatus.create_as_document_uploaded().dto,
        )

        response = client.post(
            f'/intake/analyses/{analysis.id}/petition-extraction',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 404
        assert len(fake_inngest_client.sent_events) == 0
