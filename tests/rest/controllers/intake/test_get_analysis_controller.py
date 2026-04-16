from collections.abc import Callable
from datetime import UTC

from fastapi.testclient import TestClient

from animus.database.sqlalchemy.models.intake import AnalysisModel
from tests.fixtures.auth_fixtures import CreateAccountFixture

BuildAuthHeadersFixture = Callable[[str], dict[str, str]]
CreateAnalysisFixture = Callable[..., AnalysisModel]


class TestGetAnalysisController:
    def test_should_return_200_when_analysis_belongs_to_authenticated_account(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        analysis = create_analysis(account_id=account.id)

        response = client.get(
            f'/intake/analyses/{analysis.id}',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 200
        assert response.json() == {
            'id': analysis.id,
            'name': analysis.name,
            'folder_id': analysis.folder_id,
            'account_id': account.id,
            'status': analysis.status,
            'is_archived': analysis.is_archived,
            'precedents_search_filters': None,
            'created_at': analysis.created_at.replace(tzinfo=UTC).isoformat(),
        }

    def test_should_return_404_when_analysis_belongs_to_another_account(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        create_analysis: CreateAnalysisFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        authenticated_account = create_account(
            email='ana@example.com',
            is_verified=True,
            is_active=True,
        )
        owner_account = create_account(
            email='bruna@example.com',
            is_verified=True,
            is_active=True,
        )
        analysis = create_analysis(account_id=owner_account.id)

        response = client.get(
            f'/intake/analyses/{analysis.id}',
            headers=build_auth_headers(authenticated_account.id),
        )

        assert response.status_code == 404
        assert response.json() == {
            'title': 'Not Found Error',
            'message': 'Analise nao encontrada',
        }

    def test_should_return_400_when_analysis_id_is_invalid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        build_auth_headers: BuildAuthHeadersFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)

        response = client.get(
            '/intake/analyses/invalid-analysis-id',
            headers=build_auth_headers(account.id),
        )

        assert response.status_code == 400
        assert response.json()['title'] == 'Erro de validação'
        assert 'ULID' in response.json()['message']
