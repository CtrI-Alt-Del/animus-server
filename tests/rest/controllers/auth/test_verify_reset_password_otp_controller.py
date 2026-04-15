from fastapi.testclient import TestClient

from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.fixtures.inngest_fixtures import FakeInngestClient


class TestVerifyResetPasswordOtpController:
    def test_should_return_reset_context_when_otp_is_valid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        create_account(email='maria@example.com', is_verified=True)

        forgot_response = client.post(
            '/auth/password/forgot',
            json={'email': 'maria@example.com'},
        )
        assert forgot_response.status_code == 204

        otp = fake_inngest_client.sent_events[0].data['account_email_otp']

        response = client.post(
            '/auth/password/verify-reset-otp',
            json={'email': 'maria@example.com', 'otp': otp},
        )

        assert response.status_code == 200
        assert response.json()['reset_context']

    def test_should_return_401_when_otp_is_invalid(self, client: TestClient) -> None:
        response = client.post(
            '/auth/password/verify-reset-otp',
            json={'email': 'maria@example.com', 'otp': '000000'},
        )

        assert response.status_code == 401
        assert response.json() == {
            'title': 'Erro de autenticação',
            'message': 'Codigo OTP de reset de senha invalido ou expirado',
        }

    def test_should_return_422_when_payload_is_missing(
        self,
        client: TestClient,
    ) -> None:
        response = client.post('/auth/password/verify-reset-otp', json={})

        assert response.status_code == 422
