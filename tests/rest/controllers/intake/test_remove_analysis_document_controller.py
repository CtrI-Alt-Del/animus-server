from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.database.sqlalchemy.models.intake import (
    AnalysisDocumentModel,
    AnalysisModel,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.rest.controllers.intake.conftest import BuildAuthHeadersFixture


def _create_analysis_with_document(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    account_id: str,
) -> str:
    analysis_id = str(ULID())
    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Análise',
            folder_id=None,
            account_id=account_id,
            type='FIRST_INSTANCE',
            status='DOCUMENT_UPLOADED',
            is_archived=False,
            created_at=datetime.now(UTC),
        )
    )
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

    return analysis_id


class TestRemoveAnalysisDocumentController:
    def test_should_return_204_remove_document_and_reset_analysis_status(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_analysis_with_document(
            sqlalchemy_session_factory,
            account_id=account.id,
        )

        response = client.delete(
            f'/intake/analyses/{analysis_id}/documents',
            params={'file_path': 'intake/analyses/document.pdf'},
            headers=build_auth_headers(account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        persisted_document = inspection_session.scalar(
            select(AnalysisDocumentModel).where(
                AnalysisDocumentModel.analysis_id == analysis_id
            )
        )
        persisted_analysis = inspection_session.scalar(
            select(AnalysisModel).where(AnalysisModel.id == analysis_id)
        )
        inspection_session.close()

        assert response.status_code == 204
        assert response.content == b''
        assert persisted_document is None
        assert persisted_analysis is not None
        assert persisted_analysis.status == 'WAITING_DOCUMENT_UPLOAD'

    def test_should_return_404_when_file_path_does_not_match_document(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id = _create_analysis_with_document(
            sqlalchemy_session_factory,
            account_id=account.id,
        )

        response = client.delete(
            f'/intake/analyses/{analysis_id}/documents',
            params={'file_path': 'intake/analyses/other-document.pdf'},
            headers=build_auth_headers(account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        persisted_document = inspection_session.scalar(
            select(AnalysisDocumentModel).where(
                AnalysisDocumentModel.analysis_id == analysis_id
            )
        )
        inspection_session.close()

        assert response.status_code == 404
        assert persisted_document is not None

    def test_should_return_422_when_file_path_query_param_is_missing(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)

        response = client.delete(
            f'/intake/analyses/{ULID()!s}/documents',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 422
