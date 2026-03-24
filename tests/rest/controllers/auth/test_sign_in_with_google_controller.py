from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from animus.core.auth.domain.structures.email import Email
from animus.core.shared.domain.structures.text import Text
from animus.database.sqlalchemy.models.auth import AccountModel
from tests.fixtures.auth_fixtures import CreateAccountFixture


class TestSignInWithGoogleController:
    @patch('animus.providers.auth.google.google_oauth_provider.GoogleOAuthProvider.get_user_info')
    def test_should_return_201_and_persist_account_when_account_does_not_exist(
        self,
        mock_get_user_info: MagicMock,
        client: TestClient,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> None:
        mock_get_user_info.return_value = (Text.create('Maria Google'), Email.create('maria.google@example.com'))
        payload = {'id_token': 'valid_mocked_id_token'}

        response = client.post('/auth/sign-up/google', json=payload)

        if response.status_code != 201:
            print("ERRO DA API:", response.json())
        assert response.status_code == 201

        inspection_session = sqlalchemy_session_factory()
        persisted_account = inspection_session.scalar(
            select(AccountModel).where(AccountModel.email == 'maria.google@example.com')
        )
        inspection_session.close()

        assert persisted_account is not None
        assert persisted_account.name == 'Maria Google'
        assert persisted_account.email == 'maria.google@example.com'
        assert persisted_account.password_hash is None
        assert persisted_account.is_verified is True

        json_response = response.json()
        assert 'access_token' in json_response
        assert 'value' in json_response['access_token']
        assert 'refresh_token' in json_response

    @patch('animus.providers.auth.google.google_oauth_provider.GoogleOAuthProvider.get_user_info')
    def test_should_return_201_and_return_session_when_account_already_exists(
        self,
        mock_get_user_info,
        client: TestClient,
        create_account: CreateAccountFixture,
    ) -> None:
        email = 'maria.google@example.com'
        mock_get_user_info.return_value = (Text.create('Maria Google'), Email.create('maria.google@example.com'))
        
        create_account(email=email, name='Maria Google')

        payload = {'id_token': 'valid_mocked_id_token'}

        response = client.post('/auth/sign-up/google', json=payload)

        assert response.status_code == 201
        json_response = response.json()
        assert 'access_token' in json_response
        assert 'value' in json_response['access_token']
        assert 'refresh_token' in json_response

    def test_should_return_422_when_id_token_is_missing(
        self,
        client: TestClient,
    ) -> None:
        response = client.post('/auth/sign-up/google', json={})

        assert response.status_code == 422
