from fastapi.testclient import TestClient

from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.fixtures.inngest_fixtures import FakeInngestClient


class TestResendVerificationEmailController:
    def test_should_return_204_and_publish_event_when_account_is_not_verified(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        create_account(email='maria@example.com', is_verified=False)

        response = client.post(
            '/auth/resend-verification-email',
            json={'email': 'maria@example.com'},
        )

        assert response.status_code == 204
        assert response.content == b''
        assert len(fake_inngest_client.sent_events) == 1
        assert fake_inngest_client.sent_events[0].name == (
            'auth/email-verification.requested'
        )
        assert fake_inngest_client.sent_events[0].data['account_email'] == (
            'maria@example.com'
        )
        assert fake_inngest_client.sent_events[0].data[
            'account_email_verification_token'
        ]

    def test_should_return_409_when_account_is_already_verified(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
    ) -> None:
        create_account(email='maria@example.com', is_verified=True)

        response = client.post(
            '/auth/resend-verification-email',
            json={'email': 'maria@example.com'},
        )

        assert response.status_code == 409
        assert response.json() == {
            'title': 'Erro de conflito',
            'message': 'Conta ja verificada',
        }

    def test_should_return_422_when_email_is_missing(
        self,
        client: TestClient,
    ) -> None:
        response = client.post('/auth/resend-verification-email', json={})

        assert response.status_code == 422

    def test_should_return_404_when_account_does_not_exist(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(
            '/auth/resend-verification-email',
            json={'email': 'missing@example.com'},
        )

        assert response.status_code == 404
        assert response.json() == {
            'title': 'Not Found Error',
            'message': 'Conta nao encontrada',
        }
