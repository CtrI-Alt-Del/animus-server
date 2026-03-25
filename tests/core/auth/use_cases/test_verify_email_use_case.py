from datetime import UTC, datetime, timedelta
from unittest.mock import create_autospec

import pytest

from animus.constants.cache_keys import CacheKeys
from animus.core.auth.domain.entities import Account
from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.domain.errors import (
    AccountNotFoundError,
    InvalidEmailVerificationTokenError,
)
from animus.core.auth.domain.structures import Session
from animus.core.auth.domain.structures.dtos import SessionDto, TokenDto
from animus.core.auth.interfaces import (
    AccountsRepository,
    JwtProvider,
)
from animus.core.auth.use_cases import VerifyEmailUseCase
from animus.core.shared.domain.structures import Text
from animus.core.shared.interfaces import CacheProvider


class TestVerifyEmailUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.accounts_repository_mock = create_autospec(
            AccountsRepository,
            instance=True,
        )
        self.cache_provider_mock = create_autospec(
            CacheProvider,
            instance=True,
        )
        self.jwt_provider_mock = create_autospec(JwtProvider, instance=True)
        self.use_case = VerifyEmailUseCase(
            accounts_repository=self.accounts_repository_mock,
            cache_provider=self.cache_provider_mock,
            jwt_provider=self.jwt_provider_mock,
        )

    def test_should_verify_account_and_return_session_when_otp_is_valid(self) -> None:

        account = Account.create(
            AccountDto(
                id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
                name='Maria Silva',
                email='maria@example.com',
                password=None,
                is_verified=False,
                is_active=True,
                social_accounts=[],
            )
        )
        session = Session.create(
            SessionDto(
                access_token=TokenDto(
                    value='access-token',
                    expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
                ),
                refresh_token=TokenDto(
                    value='refresh-token',
                    expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
                ),
            )
        )
        self.cache_provider_mock.get.return_value = Text.create('123456')
        self.accounts_repository_mock.find_by_email.return_value = account
        self.jwt_provider_mock.encode.return_value = session

        result = self.use_case.execute(email='maria@example.com', otp='123456')

        self.accounts_repository_mock.replace.assert_called_once_with(account)
        self.cache_provider_mock.delete.assert_called_once_with(
            CacheKeys().get_email_verification('maria@example.com')
        )
        self.jwt_provider_mock.encode.assert_called_once_with(
            Text.create(account.id.value)
        )
        assert account.is_verified.is_true is True
        assert result.access_token.value == 'access-token'
        assert result.refresh_token.value == 'refresh-token'

    def test_should_raise_invalid_token_error_when_cache_value_is_missing(self) -> None:
        self.cache_provider_mock.get.return_value = None

        with pytest.raises(InvalidEmailVerificationTokenError):
            self.use_case.execute(email='maria@example.com', otp='123456')

        self.accounts_repository_mock.find_by_email.assert_not_called()
        self.accounts_repository_mock.replace.assert_not_called()
        self.cache_provider_mock.delete.assert_not_called()
        self.jwt_provider_mock.encode.assert_not_called()

    def test_should_raise_invalid_token_error_when_otp_does_not_match(self) -> None:
        self.cache_provider_mock.get.return_value = Text.create('654321')

        with pytest.raises(InvalidEmailVerificationTokenError):
            self.use_case.execute(email='maria@example.com', otp='123456')

        self.accounts_repository_mock.find_by_email.assert_not_called()
        self.accounts_repository_mock.replace.assert_not_called()
        self.cache_provider_mock.delete.assert_not_called()
        self.jwt_provider_mock.encode.assert_not_called()

    def test_should_raise_invalid_token_error_when_cached_otp_is_malformed(
        self,
    ) -> None:
        self.cache_provider_mock.get.return_value = Text.create('abc123')

        with pytest.raises(InvalidEmailVerificationTokenError):
            self.use_case.execute(email='maria@example.com', otp='123456')

        self.accounts_repository_mock.find_by_email.assert_not_called()
        self.accounts_repository_mock.replace.assert_not_called()
        self.cache_provider_mock.delete.assert_not_called()
        self.jwt_provider_mock.encode.assert_not_called()

    def test_should_raise_invalid_token_error_when_account_is_not_found(self) -> None:
        self.cache_provider_mock.get.return_value = Text.create('123456')
        self.accounts_repository_mock.find_by_email.side_effect = AccountNotFoundError()

        with pytest.raises(InvalidEmailVerificationTokenError):
            self.use_case.execute(email='maria@example.com', otp='123456')

        self.accounts_repository_mock.replace.assert_not_called()
        self.cache_provider_mock.delete.assert_not_called()
        self.jwt_provider_mock.encode.assert_not_called()
