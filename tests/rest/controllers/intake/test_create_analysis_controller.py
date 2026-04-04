from collections.abc import Callable
from datetime import UTC

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from animus.database.sqlalchemy.models.intake import AnalysisModel
from tests.fixtures.auth_fixtures import CreateAccountFixture

BuildAuthHeadersFixture = Callable[[str], dict[str, str]]
CreateAnalysisFixture = Callable[..., AnalysisModel]


class TestCreateAnalysisController:
    def test_should_return_201_and_persist_analysis_with_generated_name(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
        build_auth_headers: BuildAuthHeadersFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        create_analysis(account_id=account.id, name='Nova analise #1')
        create_analysis(account_id=account.id, name='Nova analise #2')

        response = client.post(
            '/intake/analyses',
            json={'folder_id': '01BX5ZZKBKACTAV9WEVGEMMVRZ'},
            headers=build_auth_headers(account.id),
        )

        inspection_session = sqlalchemy_session_factory()
        persisted_analysis = inspection_session.scalar(
            select(AnalysisModel).where(
                AnalysisModel.account_id == account.id,
                AnalysisModel.name == 'Nova analise #3',
            )
        )
        inspection_session.close()

        assert response.status_code == 201
        assert persisted_analysis is not None
        assert response.json() == {
            'id': persisted_analysis.id,
            'name': 'Nova analise #3',
            'folder_id': '01BX5ZZKBKACTAV9WEVGEMMVRZ',
            'account_id': account.id,
            'status': 'WAITING_PETITION',
            'is_archived': False,
            'created_at': persisted_analysis.created_at.replace(tzinfo=UTC).isoformat(),
        }

    def test_should_return_400_when_folder_id_is_invalid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)

        response = client.post(
            '/intake/analyses',
            json={'folder_id': 'invalid-folder-id'},
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 400
        assert response.json()['title'] == 'Erro de validação'
        assert 'ULID' in response.json()['message']
