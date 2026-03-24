from unittest.mock import ANY, MagicMock, create_autospec

import pytest

from animus.core.auth.domain.structures.dtos.session_dto import SessionDto
from animus.core.auth.domain.structures.dtos.token_dto import TokenDto
from animus.core.auth.domain.structures.email import Email
from animus.core.auth.interfaces.accounts_repository import AccountsRepository
from animus.core.auth.interfaces.oauth_provider import OAuthProvider
from animus.core.auth.interfaces.jwt_provider import JwtProvider
from animus.core.auth.use_cases.sign_in_with_google_use_case import SignInWithGoogleUseCase
from animus.core.shared.domain.structures.text import Text


class TestSignInWithGoogleUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.accounts_repository_mock = create_autospec(
            AccountsRepository,
            instance=True,
        )
        self.jwt_provider_mock = create_autospec(
            JwtProvider,
            instance=True,
        )
        self.google_oauth_provider_mock = create_autospec(
            OAuthProvider,
            instance=True,
        )
        self.use_case = SignInWithGoogleUseCase(
            accounts_repository=self.accounts_repository_mock,
            jwt_provider=self.jwt_provider_mock,
            google_oauth_provider=self.google_oauth_provider_mock,
        )

        self.mock_access_token = TokenDto(value='access_token', expires_at='2026-12-31T23:59:59Z')
        self.mock_refresh_token = TokenDto(value='refresh_token', expires_at='2026-12-31T23:59:59Z')
        self.expected_session = SessionDto(
            access_token=self.mock_access_token,
            refresh_token=self.mock_refresh_token
        )
        
        self.mock_encoded_result = MagicMock()
        self.mock_encoded_result.dto = self.expected_session

    def test_should_create_account_and_link_social_when_account_does_not_exist(self) -> None:
        id_token = 'test_id_token'
        name = 'Test User'
        email_str = 'test@example.com'

        self.google_oauth_provider_mock.get_user_info.return_value = (Text.create(name), Email.create(email_str))
        self.accounts_repository_mock.try_to_find_by_email.return_value = None
        self.jwt_provider_mock.encode.return_value = self.mock_encoded_result

        result = self.use_case.execute(id_token)

        self.google_oauth_provider_mock.get_user_info.assert_called_once_with(Text.create(id_token))
        self.accounts_repository_mock.try_to_find_by_email.assert_called_once_with(Email.create(email_str))
        
        self.accounts_repository_mock.add.assert_called_once_with(ANY, None)
        self.jwt_provider_mock.encode.assert_called_once()
        assert result == self.expected_session

    def test_should_link_social_account_and_replace_when_account_exists_but_not_linked(self) -> None:
        id_token = 'test_id_token'
        name = 'Test User'
        email_str = 'test@example.com'
        account_id_str = 'account-123'

        existing_account_mock = MagicMock()
        existing_account_mock.id.value = account_id_str
        existing_account_mock.name.value = name
        existing_account_mock.email.value = email_str
        
        social_accounts_mock = MagicMock()
        social_accounts_mock.__contains__.return_value = False
        existing_account_mock.social_accounts = social_accounts_mock

        self.google_oauth_provider_mock.get_user_info.return_value = (name, email_str)
        self.accounts_repository_mock.try_to_find_by_email.return_value = existing_account_mock
        self.jwt_provider_mock.encode.return_value = self.mock_encoded_result

        result = self.use_case.execute(id_token)

        existing_account_mock.add_social_account.assert_called_once_with(ANY)
        self.accounts_repository_mock.replace.assert_called_once_with(existing_account_mock)
        self.jwt_provider_mock.encode.assert_called_once_with(Text.create(account_id_str))
        assert result == self.expected_session

    def test_should_only_return_session_when_account_exists_and_already_linked(self) -> None:
        id_token = 'test_id_token'
        name = 'Test User'
        email_str = 'test@example.com'
        account_id_str = 'account-123'

        existing_account_mock = MagicMock()
        existing_account_mock.id.value = account_id_str
        existing_account_mock.name.value = name
        existing_account_mock.email.value = email_str
        
        social_accounts_mock = MagicMock()
        social_accounts_mock.__contains__.return_value = True
        existing_account_mock.social_accounts = social_accounts_mock

        self.google_oauth_provider_mock.get_user_info.return_value = (name, email_str)
        self.accounts_repository_mock.try_to_find_by_email.return_value = existing_account_mock
        self.jwt_provider_mock.encode.return_value = self.mock_encoded_result

        result = self.use_case.execute(id_token)

        existing_account_mock.add_social_account.assert_not_called()
        self.accounts_repository_mock.replace.assert_not_called()
        self.jwt_provider_mock.encode.assert_called_once_with(Text.create(account_id_str))
        assert result == self.expected_session
