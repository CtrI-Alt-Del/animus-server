from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from animus.database.sqlalchemy.models.intake import AnalysisDocumentModel
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.rest.controllers.intake.conftest import (
    BuildAuthHeadersFixture,
    CreateAnalysisFixture,
)


class TestListAnalysisDocumentsController:
    def test_should_return_200_and_analysis_documents_when_documents_exist(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        create_analysis: CreateAnalysisFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(account_id=account.id)
        session = sqlalchemy_session_factory()
        session.add_all(
            [
                AnalysisDocumentModel(
                    analysis_id=analysis.id,
                    uploaded_at=datetime(2026, 3, 27, 10, 30, tzinfo=UTC),
                    document_file_path='intake/analyses/document-1.pdf',
                    document_name='document-1.pdf',
                ),
                AnalysisDocumentModel(
                    analysis_id=analysis.id,
                    uploaded_at=datetime(2026, 3, 28, 10, 30, tzinfo=UTC),
                    document_file_path='intake/analyses/document-2.pdf',
                    document_name='document-2.pdf',
                ),
            ]
        )
        session.commit()
        session.close()

        response = client.get(
            f'/intake/analyses/{analysis.id}/documents/all',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 200
        assert response.json() == [
            {
                'analysis_id': analysis.id,
                'uploaded_at': '2026-03-27T10:30:00+00:00',
                'file_path': 'intake/analyses/document-1.pdf',
                'name': 'document-1.pdf',
            },
            {
                'analysis_id': analysis.id,
                'uploaded_at': '2026-03-28T10:30:00+00:00',
                'file_path': 'intake/analyses/document-2.pdf',
                'name': 'document-2.pdf',
            },
        ]

    def test_should_return_422_when_analysis_id_is_invalid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)

        response = client.get(
            '/intake/analyses/invalid-analysis-id/documents/all',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 422
