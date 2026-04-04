from fastapi.testclient import TestClient

from tests.fixtures.auth_fixtures import CreateAccountFixture


class TestResetPasswordController:
    def test_should_return_success_when_password_is_reset(
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
        response = client.post(
            '/auth/password/reset',
            json={
                'account_id': account.id,
                'new_password': 'StrongPassword123'
            },
        )
        assert response.status_code == 200

    def test_should_return_404_when_account_does_not_exist(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(
            '/auth/password/reset',
            json={
                'account_id': 'non-existent-account-id',
                'new_password': 'StrongPassword123'
            },
        )
        assert response.status_code == 400

    def test_should_return_422_when_missing_account_id(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(
            '/auth/password/reset',
            json={
                'new_password': 'StrongPassword123'
            },
        )
        assert response.status_code == 422

    def test_should_return_422_when_missing_new_password(
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
        response = client.post(
            '/auth/password/reset',
            json={
                'account_id': account.id
            },
        )
        assert response.status_code == 422
