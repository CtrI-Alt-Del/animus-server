from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from animus.database.sqlalchemy.models.auth import AccountModel
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.fixtures.inngest_fixtures import FakeInngestClient


class TestVerifyEmailController:
    def test_should_return_session_and_verify_account_when_otp_is_valid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        fake_inngest_client: FakeInngestClient,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        create_account(email='maria@example.com', is_verified=False)

        resend_response = client.post(
            '/auth/resend-verification-email',
            json={'email': 'maria@example.com'},
        )
        assert resend_response.status_code == 204
        assert len(fake_inngest_client.sent_events) == 1

        otp = fake_inngest_client.sent_events[0].data['account_email_otp']

        response = client.post(
            '/auth/verify-email',
            json={'email': 'maria@example.com', 'otp': otp},
        )
        json_response = response.json()

        inspection_session = sqlalchemy_session_factory()
        refreshed_account = inspection_session.scalar(
            select(AccountModel).where(AccountModel.email == 'maria@example.com')
        )
        inspection_session.close()

        assert response.status_code == 200
        assert json_response['access_token']['value']
        assert json_response['access_token']['expires_at']
        assert json_response['refresh_token']['value']
        assert json_response['refresh_token']['expires_at']
        assert refreshed_account is not None
        assert refreshed_account.is_verified is True

    def test_should_return_401_when_token_is_invalid(self, client: TestClient) -> None:
        response = client.post(
            '/auth/verify-email',
            json={'email': 'maria@example.com', 'otp': '000000'},
        )

        assert response.status_code == 401
        assert response.json() == {
            'title': 'Erro de autenticação',
            'message': 'Codigo OTP de verificacao de email invalido ou expirado',
        }

    def test_should_return_422_when_payload_is_missing(
        self, client: TestClient
    ) -> None:
        response = client.post('/auth/verify-email', json={})

        assert response.status_code == 422
