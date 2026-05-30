from unittest.mock import MagicMock, create_autospec

import pytest

from animus.core.auth.domain.entities import Account
from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.domain.errors import (
    AccountInactiveError,
    AccountNotVerifiedError,
    InvalidRefreshTokenError,
)
from animus.core.auth.domain.structures.dtos import SessionDto, TokenDto
from animus.core.auth.interfaces import AccountsRepository, JwtProvider
from animus.core.auth.use_cases import RefreshSessionUseCase
from animus.core.shared.domain.structures import Id, Text


class TestRefreshSessionUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.accounts_repository_mock = create_autospec(
            AccountsRepository,
            instance=True,
        )
        self.jwt_provider_mock = create_autospec(JwtProvider, instance=True)
        self.use_case = RefreshSessionUseCase(
            accounts_repository=self.accounts_repository_mock,
            jwt_provider=self.jwt_provider_mock,
        )

        self.expected_session = SessionDto(
            access_token=TokenDto(
                value='new-access-token',
                expires_at='2026-12-31T23:59:59+00:00',
            ),
            refresh_token=TokenDto(
                value='new-refresh-token',
                expires_at='2027-01-31T23:59:59+00:00',
            ),
        )
        self.encoded_session_mock = MagicMock()
        self.encoded_session_mock.dto = self.expected_session

    def test_should_return_new_session_when_refresh_token_is_valid(self) -> None:
        refresh_token = 'valid-refresh-token'
        account = self._create_account(is_verified=True, is_active=True)
        self.jwt_provider_mock.decode.return_value = {
            'type': 'refresh',
            'sub': account.id.value,
        }
        self.accounts_repository_mock.find_by_id.return_value = account
        self.jwt_provider_mock.encode.return_value = self.encoded_session_mock

        result = self.use_case.execute(refresh_token=refresh_token)

        self.jwt_provider_mock.decode.assert_called_once_with(
            Text.create(refresh_token)
        )
        self.accounts_repository_mock.find_by_id.assert_called_once_with(
            Id.create(account.id.value)
        )
        self.jwt_provider_mock.encode.assert_called_once_with(
            Text.create(account.id.value)
        )
        assert result == self.expected_session

    def test_should_raise_invalid_refresh_token_error_when_decode_fails(self) -> None:
        refresh_token = 'invalid-token'
        self.jwt_provider_mock.decode.side_effect = RuntimeError('decode error')

        with pytest.raises(InvalidRefreshTokenError):
            self.use_case.execute(refresh_token=refresh_token)

        self.accounts_repository_mock.find_by_id.assert_not_called()
        self.jwt_provider_mock.encode.assert_not_called()

    def test_should_raise_invalid_refresh_token_error_when_token_is_blank(self) -> None:
        with pytest.raises(InvalidRefreshTokenError):
            self.use_case.execute(refresh_token='')

        self.accounts_repository_mock.find_by_id.assert_not_called()
        self.jwt_provider_mock.encode.assert_not_called()

    def test_should_raise_invalid_refresh_token_error_when_type_is_not_refresh(
        self,
    ) -> None:
        refresh_token = 'token-with-access-type'
        self.jwt_provider_mock.decode.return_value = {
            'type': 'access',
            'sub': '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        }

        with pytest.raises(InvalidRefreshTokenError):
            self.use_case.execute(refresh_token=refresh_token)

        self.accounts_repository_mock.find_by_id.assert_not_called()
        self.jwt_provider_mock.encode.assert_not_called()

    def test_should_raise_invalid_refresh_token_error_when_sub_is_missing(self) -> None:
        refresh_token = 'token-without-sub'
        self.jwt_provider_mock.decode.return_value = {'type': 'refresh'}

        with pytest.raises(InvalidRefreshTokenError):
            self.use_case.execute(refresh_token=refresh_token)

        self.accounts_repository_mock.find_by_id.assert_not_called()
        self.jwt_provider_mock.encode.assert_not_called()

    def test_should_raise_invalid_refresh_token_error_when_sub_is_invalid(self) -> None:
        refresh_token = 'token-with-invalid-sub'
        self.jwt_provider_mock.decode.return_value = {
            'type': 'refresh',
            'sub': 'invalid-ulid',
        }

        with pytest.raises(InvalidRefreshTokenError):
            self.use_case.execute(refresh_token=refresh_token)

        self.accounts_repository_mock.find_by_id.assert_not_called()
        self.jwt_provider_mock.encode.assert_not_called()

    def test_should_raise_invalid_refresh_token_error_when_account_does_not_exist(
        self,
    ) -> None:
        refresh_token = 'token-with-unknown-account'
        account_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        self.jwt_provider_mock.decode.return_value = {
            'type': 'refresh',
            'sub': account_id,
        }
        self.accounts_repository_mock.find_by_id.return_value = None

        with pytest.raises(InvalidRefreshTokenError):
            self.use_case.execute(refresh_token=refresh_token)

        self.accounts_repository_mock.find_by_id.assert_called_once_with(
            Id.create(account_id)
        )
        self.jwt_provider_mock.encode.assert_not_called()

    def test_should_raise_account_not_verified_error_when_account_is_not_verified(
        self,
    ) -> None:
        refresh_token = 'token-for-unverified-account'
        account = self._create_account(is_verified=False, is_active=True)
        self.jwt_provider_mock.decode.return_value = {
            'type': 'refresh',
            'sub': account.id.value,
        }
        self.accounts_repository_mock.find_by_id.return_value = account

        with pytest.raises(AccountNotVerifiedError):
            self.use_case.execute(refresh_token=refresh_token)

        self.accounts_repository_mock.find_by_id.assert_called_once_with(
            Id.create(account.id.value)
        )
        self.jwt_provider_mock.encode.assert_not_called()

    def test_should_raise_account_inactive_error_when_account_is_inactive(self) -> None:
        refresh_token = 'token-for-inactive-account'
        account = self._create_account(is_verified=True, is_active=False)
        self.jwt_provider_mock.decode.return_value = {
            'type': 'refresh',
            'sub': account.id.value,
        }
        self.accounts_repository_mock.find_by_id.return_value = account

        with pytest.raises(AccountInactiveError):
            self.use_case.execute(refresh_token=refresh_token)

        self.accounts_repository_mock.find_by_id.assert_called_once_with(
            Id.create(account.id.value)
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
