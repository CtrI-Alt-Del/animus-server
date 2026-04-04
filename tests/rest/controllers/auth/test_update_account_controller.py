from fastapi.testclient import TestClient

from animus.core.shared.domain.structures import Text
from animus.providers.auth.jwt.jose.jose_jwt_provider import JoseJwtProvider
from tests.fixtures.auth_fixtures import CreateAccountFixture


class TestUpdateAccountController:
    def test_should_return_200_and_account_dto_when_update_is_successful(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
    ) -> None:
        account = create_account(name='Nome Antigo', is_verified=True, is_active=True)
        token = JoseJwtProvider().encode(Text.create(account.id)).dto.access_token.value

        response = client.patch(
            '/auth/account',
            json={'name': 'Novo Nome'},
            headers={'Authorization': f'Bearer {token}'},
        )

        assert response.status_code == 200
        assert response.json()['name'] == 'Novo Nome'
        assert response.json()['id'] == account.id

    def test_should_return_401_when_not_authenticated(
        self,
        client: TestClient,
    ) -> None:
        response = client.patch(
            '/auth/account',
            json={'name': 'Novo Nome'},
        )

        assert response.status_code == 401

    def test_should_return_400_when_name_is_invalid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
    ) -> None:
        account = create_account(name='Nome Antigo', is_verified=True, is_active=True)
        token = JoseJwtProvider().encode(Text.create(account.id)).dto.access_token.value

        response = client.patch(
            '/auth/account',
            json={'name': 'A'},  # Invalid name (too short)
            headers={'Authorization': f'Bearer {token}'},
        )

        assert response.status_code == 400
        assert response.json()['title'] == 'Erro de validação'

    def test_should_return_422_when_payload_is_missing_required_fields(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
    ) -> None:
        account = create_account(is_verified=True, is_active=True)
        token = JoseJwtProvider().encode(Text.create(account.id)).dto.access_token.value

        response = client.patch(
            '/auth/account',
            json={},
            headers={'Authorization': f'Bearer {token}'},
        )

        assert response.status_code == 422
