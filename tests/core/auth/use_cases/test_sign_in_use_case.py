from unittest.mock import MagicMock, create_autospec

import pytest

from animus.core.auth.domain.entities import Account
from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.domain.errors import (
    AccountInactiveError,
    AccountNotFoundError,
    AccountNotVerifiedError,
    InvalidCredentialsError,
)
from animus.core.auth.domain.structures.dtos import SessionDto, TokenDto
from animus.core.auth.interfaces import AccountsRepository, HashProvider, JwtProvider
from animus.core.auth.use_cases import SignInUseCase
from animus.core.shared.domain.structures import Logical, Text


class TestSignInUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.accounts_repository_mock = create_autospec(
            AccountsRepository,
            instance=True,
        )
        self.hash_provider_mock = create_autospec(HashProvider, instance=True)
        self.jwt_provider_mock = create_autospec(JwtProvider, instance=True)
        self.use_case = SignInUseCase(
            accounts_repository=self.accounts_repository_mock,
            hash_provider=self.hash_provider_mock,
            jwt_provider=self.jwt_provider_mock,
        )

        self.expected_session = SessionDto(
            access_token=TokenDto(
                value='access-token',
                expires_at='2026-12-31T23:59:59+00:00',
            ),
            refresh_token=TokenDto(
                value='refresh-token',
                expires_at='2027-01-31T23:59:59+00:00',
            ),
        )
        self.encoded_session_mock = MagicMock()
        self.encoded_session_mock.dto = self.expected_session

    def test_should_return_session_when_credentials_are_valid(self) -> None:
        valid_password = 'Password123'  # noqa: S105
        account = self._create_account(is_verified=True, is_active=True)
        password_hash = Text.create('stored-password-hash')

        self.accounts_repository_mock.find_by_email.return_value = account
        self.accounts_repository_mock.find_password_hash_by_email.return_value = (
            password_hash
        )
        self.hash_provider_mock.verify.return_value = Logical.create_true()
        self.jwt_provider_mock.encode.return_value = self.encoded_session_mock

        result = self.use_case.execute(
            email='maria@example.com',
            password=valid_password,
        )

        self.accounts_repository_mock.find_by_email.assert_called_once_with(
            account.email
        )
        self.accounts_repository_mock.find_password_hash_by_email.assert_called_once_with(
            account.email
        )
        self.hash_provider_mock.verify.assert_called_once_with(
            Text.create(valid_password),
            password_hash,
        )
        self.jwt_provider_mock.encode.assert_called_once_with(
            Text.create(account.id.value)
        )
        assert result == self.expected_session

    def test_should_raise_invalid_credentials_error_when_account_does_not_exist(
        self,
    ) -> None:
        valid_password = 'Password123'  # noqa: S105
        self.accounts_repository_mock.find_by_email.side_effect = AccountNotFoundError()

        with pytest.raises(InvalidCredentialsError):
            self.use_case.execute(
                email='maria@example.com',
                password=valid_password,
            )

        self.accounts_repository_mock.find_password_hash_by_email.assert_not_called()
        self.hash_provider_mock.verify.assert_not_called()
        self.jwt_provider_mock.encode.assert_not_called()

    def test_should_raise_invalid_credentials_error_when_password_hash_is_missing(
        self,
    ) -> None:
        valid_password = 'Password123'  # noqa: S105
        account = self._create_account(is_verified=True, is_active=True)

        self.accounts_repository_mock.find_by_email.return_value = account
        self.accounts_repository_mock.find_password_hash_by_email.return_value = None

        with pytest.raises(InvalidCredentialsError):
            self.use_case.execute(
                email='maria@example.com',
                password=valid_password,
            )

        self.hash_provider_mock.verify.assert_not_called()
        self.jwt_provider_mock.encode.assert_not_called()

    def test_should_raise_invalid_credentials_error_when_password_is_incorrect(
        self,
    ) -> None:
        invalid_password = 'WrongPassword123'  # noqa: S105
        account = self._create_account(is_verified=True, is_active=True)
        password_hash = Text.create('stored-password-hash')

        self.accounts_repository_mock.find_by_email.return_value = account
        self.accounts_repository_mock.find_password_hash_by_email.return_value = (
            password_hash
        )
        self.hash_provider_mock.verify.return_value = Logical.create_false()

        with pytest.raises(InvalidCredentialsError):
            self.use_case.execute(
                email='maria@example.com',
                password=invalid_password,
            )

        self.hash_provider_mock.verify.assert_called_once_with(
            Text.create(invalid_password),
            password_hash,
        )
        self.jwt_provider_mock.encode.assert_not_called()

    def test_should_raise_account_not_verified_error_when_account_is_not_verified(
        self,
    ) -> None:
        valid_password = 'Password123'  # noqa: S105
        account = self._create_account(is_verified=False, is_active=True)
        password_hash = Text.create('stored-password-hash')

        self.accounts_repository_mock.find_by_email.return_value = account
        self.accounts_repository_mock.find_password_hash_by_email.return_value = (
            password_hash
        )
        self.hash_provider_mock.verify.return_value = Logical.create_true()

        with pytest.raises(AccountNotVerifiedError):
            self.use_case.execute(
                email='maria@example.com',
                password=valid_password,
            )

        self.jwt_provider_mock.encode.assert_not_called()

    def test_should_raise_account_inactive_error_when_account_is_inactive(
        self,
    ) -> None:
        valid_password = 'Password123'  # noqa: S105
        account = self._create_account(is_verified=True, is_active=False)
        password_hash = Text.create('stored-password-hash')

        self.accounts_repository_mock.find_by_email.return_value = account
        self.accounts_repository_mock.find_password_hash_by_email.return_value = (
            password_hash
        )
        self.hash_provider_mock.verify.return_value = Logical.create_true()

        with pytest.raises(AccountInactiveError):
            self.use_case.execute(
                email='maria@example.com',
                password=valid_password,
            )

        self.jwt_provider_mock.encode.assert_not_called()

    def _create_account(self, *, is_verified: bool, is_active: bool) -> Account:
        return Account.create(
            AccountDto(
                id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
                name='Maria Silva',
                email='maria@example.com',
                password=None,
                is_verified=is_verified,
                is_active=is_active,
                social_accounts=[],
            )
        )
