from fastapi.testclient import TestClient

from animus.core.auth.domain.structures.email import Email
from animus.providers.auth.email_verification.itsdangerous_email_provider import (
    ItsdangerousEmailVerificationProvider,
)
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
        verification_provider = ItsdangerousEmailVerificationProvider()
        token = verification_provider.generate_verification_token(
            Email.create(account.email)
        )

        response = client.get(
            '/auth/password/verify-reset-token',
            params={'token': token.value},
        )

        assert response.status_code == 200
        assert response.json() == {'account_id': account.id}

    def test_should_return_error_when_token_is_invalid(
        self,
        client: TestClient,
    ) -> None:
        response = client.get(
            '/auth/password/verify-reset-token',
            params={'token': 'invalid-or-expired-itsdangerous-token'},
        )

        assert response.status_code in [400, 401]

    def test_should_return_422_when_token_is_missing(
        self,
        client: TestClient,
    ) -> None:
        response = client.get(
            '/auth/password/verify-reset-token',
        )

        assert response.status_code == 422
