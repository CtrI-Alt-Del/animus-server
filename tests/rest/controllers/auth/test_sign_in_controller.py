from fastapi.testclient import TestClient

from animus.core.shared.domain.structures import Text
from animus.providers.auth.hash.argon2id_hash_provider import Argon2idHashProvider
from tests.fixtures.auth_fixtures import CreateAccountFixture


class TestSignInController:
    def test_should_return_200_and_session_when_credentials_are_valid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
    ) -> None:
        password = 'Password123'
        password_hash = Argon2idHashProvider().generate(Text.create(password)).value

        create_account(
            email='maria@example.com',
            password_hash=password_hash,
            is_verified=True,
            is_active=True,
        )
        payload = {
            'email': 'maria@example.com',
            'password': password,
        }

        response = client.post('/auth/sign-in', json=payload)
        json_response = response.json()

        assert response.status_code == 200
        assert json_response['access_token']['value']
        assert json_response['access_token']['expires_at']
        assert json_response['refresh_token']['value']
        assert json_response['refresh_token']['expires_at']

    def test_should_return_401_when_credentials_are_invalid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
    ) -> None:
        create_account(
            email='maria@example.com',
            password_hash=None,
            is_verified=True,
            is_active=True,
        )

        response = client.post(
            '/auth/sign-in',
            json={
                'email': 'maria@example.com',
                'password': 'Password123',
            },
        )

        assert response.status_code == 401
        assert response.json() == {
            'title': 'Erro de autenticação',
            'message': 'E-mail ou senha incorretos',
        }

    def test_should_return_403_when_email_is_not_confirmed(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
    ) -> None:
        password = 'Password123'
        password_hash = Argon2idHashProvider().generate(Text.create(password)).value

        create_account(
            email='maria@example.com',
            password_hash=password_hash,
            is_verified=False,
            is_active=True,
        )

        response = client.post(
            '/auth/sign-in',
            json={
                'email': 'maria@example.com',
                'password': password,
            },
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
        password = 'Password123'
        password_hash = Argon2idHashProvider().generate(Text.create(password)).value

        create_account(
            email='maria@example.com',
            password_hash=password_hash,
            is_verified=True,
            is_active=False,
        )

        response = client.post(
            '/auth/sign-in',
            json={
                'email': 'maria@example.com',
                'password': password,
            },
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
        response = client.post(
            '/auth/sign-in',
            json={
                'email': 'maria@example.com',
            },
        )

        assert response.status_code == 422
