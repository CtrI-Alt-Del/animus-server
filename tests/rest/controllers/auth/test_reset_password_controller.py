from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from animus.database.sqlalchemy.models.auth import AccountModel
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.fixtures.inngest_fixtures import FakeInngestClient


class TestResetPasswordController:
    def test_should_return_success_when_password_is_reset(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        fake_inngest_client: FakeInngestClient,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        create_account(
            name='Maria Silva',
            email='maria@example.com',
            is_active=True,
            is_verified=True,
        )

        forgot_response = client.post(
            '/auth/password/forgot',
            json={'email': 'maria@example.com'},
        )
        assert forgot_response.status_code == 204

        otp = fake_inngest_client.sent_events[0].data['account_email_otp']
        verify_response = client.post(
            '/auth/password/verify-reset-otp',
            json={'email': 'maria@example.com', 'otp': otp},
        )
        reset_context = verify_response.json()['reset_context']

        response = client.post(
            '/auth/password/reset',
            json={
                'reset_context': reset_context,
                'new_password': 'StrongPassword123',
            },
        )

        inspection_session = sqlalchemy_session_factory()
        refreshed_account = inspection_session.scalar(
            select(AccountModel).where(AccountModel.email == 'maria@example.com')
        )
        inspection_session.close()

        assert response.status_code == 200
        assert refreshed_account is not None
        assert refreshed_account.password_hash != 'stored-hash'

    def test_should_return_401_when_reset_context_is_invalid(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(
            '/auth/password/reset',
            json={
                'reset_context': 'invalid-reset-context',
                'new_password': 'StrongPassword123',
            },
        )
        assert response.status_code == 401
        assert response.json() == {
            'title': 'Erro de autenticação',
            'message': 'Contexto de reset de senha invalido ou expirado',
        }

    def test_should_return_422_when_missing_reset_context(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(
            '/auth/password/reset',
            json={'new_password': 'StrongPassword123'},
        )
        assert response.status_code == 422

    def test_should_return_422_when_missing_new_password(
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
            '/auth/password/reset',
            json={'reset_context': '01ARZ3NDEKTSV4RRFFQ69G5FAV'},
        )
        assert response.status_code == 422
