from fastapi.testclient import TestClient

from tests.fixtures.auth_fixtures import CreateAccountFixture


class TestForgotPasswordController:
    def test_should_return_204_when_account_exists(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
    ) -> None:
        create_account(
            name='Maria Silva',
            email='maria@example.com',
            is_active=True,
            is_verified=True,
        )
        response = client.post(
            '/auth/password/forgot',
            json={'email': 'maria@example.com'},
        )
        assert response.status_code == 204
        assert response.content == b''

    def test_should_return_204_when_account_does_not_exist(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(
            '/auth/password/forgot',
            json={'email': 'ghost@example.com'},
        )

        assert response.status_code == 204
        assert response.content == b''

    def test_should_return_422_when_email_is_missing_in_body(
        self,
        client: TestClient
    ) -> None:
        response = client.post(
            '/auth/password/forgot',
            json={},
        )

        assert response.status_code == 422

    def test_should_return_422_when_email_is_invalid_type(
        self,
        client: TestClient
    ) -> None:
        response = client.post(
            '/auth/password/forgot',
            json={'email': 12345},
        )
        assert response.status_code == 422
