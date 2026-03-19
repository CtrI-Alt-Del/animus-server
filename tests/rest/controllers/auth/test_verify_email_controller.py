from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from animus.core.auth.domain.structures.email import Email
from animus.database.sqlalchemy.models.auth import AccountModel
from animus.providers.auth.email_verification.itsdangerous_email_verification_provider import (
    ItsdangerousEmailVerificationProvider,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture


class TestVerifyEmailController:
    def test_should_return_success_html_and_verify_account_when_token_is_valid(
        self,
        client: TestClient,
        create_account: CreateAccountFixture,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        account = create_account(email='maria@example.com', is_verified=False)
        provider = ItsdangerousEmailVerificationProvider()
        token = provider.generate_verification_token(Email.create(account.email))

        response = client.get('/auth/verify-email', params={'token': token.value})

        inspection_session = sqlalchemy_session_factory()
        refreshed_account = inspection_session.scalar(
            select(AccountModel).where(AccountModel.id == account.id)
        )
        inspection_session.close()

        assert response.status_code == 200
        assert response.headers['content-type'].startswith('text/html')
        assert 'Email verificado com sucesso' in response.text
        assert refreshed_account is not None
        assert refreshed_account.is_verified is True

    def test_should_return_401_when_token_is_invalid(self, client: TestClient) -> None:
        response = client.get('/auth/verify-email', params={'token': 'invalid-token'})

        assert response.status_code == 401
        assert response.json() == {
            'title': 'Erro de autenticação',
            'message': 'Token de verificacao de email invalido ou expirado',
        }

    def test_should_return_422_when_token_is_missing(self, client: TestClient) -> None:
        response = client.get('/auth/verify-email')

        assert response.status_code == 422
