from fastapi.testclient import TestClient

from animus.core.shared.domain.structures import Text
from animus.providers.auth.jwt.jose.jose_jwt_provider import JoseJwtProvider
from tests.fixtures.auth_fixtures import CreateAccountFixture


class TestVerifyResetTokenController:
    def test_should_return_account_id_when_token_is_valid(
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
        session = jwt_provider.encode(Text.create(account.email))
        response = client.post(
            '/auth/password/verify-reset-token',
            json={'token': session.access_token.value},
        )
        assert response.status_code == 200
        assert response.json() == account.id

    def test_should_return_error_when_token_is_invalid(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(
            '/auth/password/verify-reset-token',
            json={'token': 'invalid-or-expired-jwt-token'},
        )
        assert response.status_code in [400, 401]

    def test_should_return_422_when_token_is_missing_in_body(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(
            '/auth/password/verify-reset-token',
            json={},
        )
        assert response.status_code == 422
