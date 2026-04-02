from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.database.sqlalchemy.models.intake import AnalysisModel, PetitionModel
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.rest.controllers.intake.conftest import BuildAuthHeadersFixture


def _create_analysis_with_petition(
    sqlalchemy_session_factory: sessionmaker[Session],
    *,
    account_id: str,
) -> tuple[str, str]:
    analysis_id = str(ULID())
    petition_id = str(ULID())
    session = sqlalchemy_session_factory()
    session.add(
        AnalysisModel(
            id=analysis_id,
            name='Analise de peticao',
            folder_id=None,
            account_id=account_id,
            status=AnalysisStatusValue.PETITION_UPLOADED.value,
            is_archived=False,
            created_at=datetime.now(UTC),
        )
    )
    session.add(
        PetitionModel(
            id=petition_id,
            analysis_id=analysis_id,
            uploaded_at=datetime(2026, 3, 27, 10, 30, tzinfo=UTC),
            document_file_path='petitions/current-petition.pdf',
            document_name='Peticao atual.pdf',
        )
    )
    session.commit()
    session.close()

    return analysis_id, petition_id


class TestGetAnalysisPetitionController:
    def test_should_return_200_and_petition_payload_when_analysis_has_petition(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis_id, petition_id = _create_analysis_with_petition(
            sqlalchemy_session_factory,
            account_id=account.id,
        )

        response = client.get(
            f'/intake/analyses/{analysis_id}/petition',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 200
        assert response.json() == {
            'id': petition_id,
            'analysis_id': analysis_id,
            'uploaded_at': '2026-03-27T10:30:00+00:00',
            'document': {
                'file_path': 'petitions/current-petition.pdf',
                'name': 'Peticao atual.pdf',
            },
        }

    def test_should_return_422_when_analysis_id_is_invalid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)

        response = client.get(
            '/intake/analyses/invalid-analysis-id/petition',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 422
