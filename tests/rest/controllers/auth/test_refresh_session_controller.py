from fastapi.testclient import TestClient

from animus.core.shared.domain.structures import Text
from animus.providers.auth.jwt.jose.jose_jwt_provider import JoseJwtProvider
from tests.fixtures.auth_fixtures import CreateAccountFixture


class TestRefreshSessionController:
    def test_should_return_200_and_session_when_refresh_token_is_valid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        refresh_token = (
            JoseJwtProvider().encode(Text.create(account.id)).dto.refresh_token.value
        )

        response = client.post(
            '/auth/refresh',
            json={'refresh_token': refresh_token},
        )
        json_response = response.json()

        assert response.status_code == 200
        assert json_response['access_token']['value']
        assert json_response['access_token']['expires_at']
        assert json_response['refresh_token']['value']
        assert json_response['refresh_token']['expires_at']

    def test_should_return_401_when_refresh_token_is_invalid(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(
            '/auth/refresh',
            json={'refresh_token': 'invalid-token'},
        )

        assert response.status_code == 401
        assert response.json() == {
            'title': 'Erro de autenticação',
            'message': 'Refresh token invalido',
        }

    def test_should_return_401_when_refresh_token_is_blank(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(
            '/auth/refresh',
            json={'refresh_token': ''},
        )

        assert response.status_code == 401
        assert response.json() == {
            'title': 'Erro de autenticação',
            'message': 'Refresh token invalido',
        }

    def test_should_return_403_when_account_is_not_verified(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
    ) -> None:
        account = create_account(is_verified=False, is_active=True)
        refresh_token = (
            JoseJwtProvider().encode(Text.create(account.id)).dto.refresh_token.value
        )

        response = client.post(
            '/auth/refresh',
            json={'refresh_token': refresh_token},
        )

        assert response.status_code == 403
        assert response.json() == {
            'title': 'Erro de acesso negado',
            'message': 'E-mail nao confirmado',
        }

    def test_should_return_403_when_account_is_inactive(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=False)
        refresh_token = (
            JoseJwtProvider().encode(Text.create(account.id)).dto.refresh_token.value
        )

        response = client.post(
            '/auth/refresh',
            json={'refresh_token': refresh_token},
        )

        assert response.status_code == 403
        assert response.json() == {
            'title': 'Erro de acesso negado',
            'message': 'Conta desativada',
        }

    def test_should_return_422_when_payload_is_invalid(
        self,
        client: TestClient,
    ) -> None:
        response = client.post('/auth/refresh', json={})

        assert response.status_code == 422
