from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from animus.core.intake.domain.structures.first_instance_analysis_status import (
    FirstInstanceAnalysisStatus,
)
from animus.database.sqlalchemy.models.intake import (
    AnalysisDocumentModel,
    AnalysisModel,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.rest.controllers.intake.conftest import (
    BuildAuthHeadersFixture,
    CreateAnalysisFixture,
)


class TestCreateAnalysisDocumentController:
    def test_should_return_201_and_persist_document_when_payload_is_valid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        create_analysis: CreateAnalysisFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(account_id=account.id)

        response = client.post(
            f'/intake/analyses/{analysis.id}/documents',
            json={
                'uploaded_at': '2026-03-27T10:30:00+00:00',
                'file_path': 'intake/analyses/document.pdf',
                'name': 'document.pdf',
            },
            headers=build_auth_headers(account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        persisted_document = inspection_session.scalar(
            select(AnalysisDocumentModel).where(
                AnalysisDocumentModel.analysis_id == analysis.id
            )
        )
        persisted_analysis = inspection_session.scalar(
            select(AnalysisModel).where(AnalysisModel.id == analysis.id)
        )
        inspection_session.close()

        assert response.status_code == 201
        assert persisted_document is not None
        assert persisted_analysis is not None
        assert (
            persisted_analysis.status
            == FirstInstanceAnalysisStatus.create_as_document_uploaded().dto
        )
        assert response.json() == {
            'analysis_id': analysis.id,
            'uploaded_at': '2026-03-27T10:30:00+00:00',
            'file_path': 'intake/analyses/document.pdf',
            'name': 'document.pdf',
        }

    def test_should_return_403_when_analysis_belongs_to_another_account(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        create_analysis: CreateAnalysisFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        authenticated_account = create_account(is_verified=True, is_active=True)
        owner_account = create_account(
            email='owner@example.com',
            is_verified=True,
            is_active=True,
        )
        analysis = create_analysis(account_id=owner_account.id)

        response = client.post(
            f'/intake/analyses/{analysis.id}/documents',
            json={
                'uploaded_at': '2026-03-27T10:30:00+00:00',
                'file_path': 'intake/analyses/document.pdf',
                'name': 'document.pdf',
            },
            headers=build_auth_headers(authenticated_account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        persisted_document = inspection_session.scalar(select(AnalysisDocumentModel))
        inspection_session.close()

        assert response.status_code == 403
        assert persisted_document is None

    def test_should_return_422_when_name_is_missing(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        create_analysis: CreateAnalysisFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(account_id=account.id)

        response = client.post(
            f'/intake/analyses/{analysis.id}/documents',
            json={
                'uploaded_at': '2026-03-27T10:30:00+00:00',
                'file_path': 'intake/analyses/document.pdf',
            },
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 422
