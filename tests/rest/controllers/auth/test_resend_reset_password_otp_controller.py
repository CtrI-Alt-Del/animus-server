from fastapi.testclient import TestClient

from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.fixtures.inngest_fixtures import FakeInngestClient


class TestResendResetPasswordOtpController:
    def test_should_return_204_and_publish_event_when_cooldown_is_not_active(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        create_account(email='maria@example.com', is_verified=True)

        response = client.post(
            '/auth/password/resend-reset-otp',
            json={'email': 'maria@example.com'},
        )

        assert response.status_code == 204
        assert response.content == b''
        assert len(fake_inngest_client.sent_events) == 1
        assert (
            fake_inngest_client.sent_events[0].name == 'auth/password-reset.requested'
        )
        assert fake_inngest_client.sent_events[0].data['account_email'] == (
            'maria@example.com'
        )
        assert fake_inngest_client.sent_events[0].data['account_email_otp']

    def test_should_return_204_without_publishing_event_when_cooldown_is_active(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        fake_inngest_client: FakeInngestClient,
    ) -> None:
        create_account(email='maria@example.com', is_verified=True)

        first_response = client.post(
            '/auth/password/forgot',
            json={'email': 'maria@example.com'},
        )
        assert first_response.status_code == 204

        response = client.post(
            '/auth/password/resend-reset-otp',
            json={'email': 'maria@example.com'},
        )

        assert response.status_code == 204
        assert response.content == b''
        assert len(fake_inngest_client.sent_events) == 1

    def test_should_return_422_when_email_is_missing(self, client: TestClient) -> None:
        response = client.post('/auth/password/resend-reset-otp', json={})

        assert response.status_code == 422
