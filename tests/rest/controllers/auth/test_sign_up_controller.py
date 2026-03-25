from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from animus.database.sqlalchemy.models.auth import AccountModel
from tests.fixtures.auth_fixtures import CreateAccountFixture
from tests.fixtures.inngest_fixtures import FakeInngestClient


class TestSignUpController:
    def test_should_return_201_and_persist_account_when_payload_is_valid(
        self,
        client: TestClient,
        fake_inngest_client: FakeInngestClient,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        valid_password = 'Password123'  # noqa: S105
        payload = {
            'name': 'Maria Silva',
            'email': 'maria@example.com',
            'password': valid_password,
        }

        response = client.post('/auth/sign-up', json=payload)

        inspection_session = sqlalchemy_session_factory()
        persisted_account = inspection_session.scalar(
            select(AccountModel).where(AccountModel.email == payload['email'])
        )
        inspection_session.close()

        assert persisted_account is not None
        assert response.status_code == 201
        assert response.json() == {
            'id': persisted_account.id,
            'name': 'Maria Silva',
            'email': 'maria@example.com',
            'password': None,
            'is_verified': False,
            'is_active': True,
            'social_accounts': [],
        }
        assert persisted_account.password_hash != payload['password']
        assert len(fake_inngest_client.sent_events) == 1
        assert fake_inngest_client.sent_events[0].name == (
            'auth/email-verification.requested'
        )
        assert (
            fake_inngest_client.sent_events[0].data['account_email'] == payload['email']
        )
        assert fake_inngest_client.sent_events[0].data['account_email_otp']

    def test_should_return_409_when_email_already_exists(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
    ) -> None:
        valid_password = 'Password123'  # noqa: S105

        create_account(email='maria@example.com')

        response = client.post(
            '/auth/sign-up',
            json={
                'name': 'Maria Silva',
                'email': 'maria@example.com',
                'password': valid_password,
            },
        )

        assert response.status_code == 409
        assert response.json() == {
            'title': 'Erro de conflito',
            'message': 'Ja existe uma conta com este email',
        }

    def test_should_return_422_when_email_is_missing(
        self,
        client: TestClient,
    ) -> None:
        valid_password = 'Password123'  # noqa: S105

        response = client.post(
            '/auth/sign-up',
            json={
                'name': 'Maria Silva',
                'password': valid_password,
            },
        )

        assert response.status_code == 422

    def test_should_return_400_when_password_is_weak(
        self,
        client: TestClient,
    ) -> None:
        weak_password = 'weak'  # noqa: S105

        response = client.post(
            '/auth/sign-up',
            json={
                'name': 'Maria Silva',
                'email': 'maria@example.com',
                'password': weak_password,
            },
        )

        assert response.status_code == 400
        assert response.json() == {
            'title': 'Erro de validação',
            'message': 'Senha deve ter pelo menos 8 caracteres',
        }
