from fastapi.testclient import TestClient

from animus.core.shared.domain.structures import Text
from animus.providers.auth.jwt.jose.jose_jwt_provider import JoseJwtProvider
from tests.fixtures.auth_fixtures import CreateAccountFixture


class TestGetAccountController:
    def test_should_return_account_when_token_is_valid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
    ) -> None:
        account = create_account(
            name='Maria Silva',
            email='maria@example.com',
            is_active=True,
            is_verified=True,
        )
        jwt_provider = JoseJwtProvider()
        session = jwt_provider.encode(Text.create(account.id))

        response = client.get(
            '/auth/account',
            headers={'Authorization': f'Bearer {session.access_token.value}'},
        )

        assert response.status_code == 200
        data = response.json()
        assert data['id'] == account.id
        assert data['name'] == 'Maria Silva'
        assert data['email'] == 'maria@example.com'
        assert data['password'] is None
        assert data['is_verified'] is True
        assert data['is_active'] is True
        assert data['social_accounts'] == []

    def test_should_return_401_when_token_is_invalid(self, client: TestClient) -> None:
        response = client.get(
            '/auth/account',
            headers={'Authorization': 'Bearer invalid-token'},
        )

        assert response.status_code == 401
        assert response.json() == {
            'title': 'Erro de autenticação',
            'message': 'Token de acesso invalido',
        }

    def test_should_return_422_when_no_token_provided(self, client: TestClient) -> None:
        response = client.get('/auth/account')

        assert response.status_code == 422
