from unittest.mock import call
from unittest.mock import create_autospec

import pytest

from animus.constants.cache_keys import CacheKeys
from animus.core.auth.domain.entities import Account
from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.domain.errors import InvalidResetPasswordOtpError
from animus.core.auth.interfaces import AccountsRepository
from animus.core.auth.use_cases import VerifyResetPasswordOtpUseCase
from animus.core.shared.domain.structures import Text, Ttl
from animus.core.shared.interfaces import CacheProvider


class TestVerifyResetPasswordOtpUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.accounts_repository_mock = create_autospec(
            AccountsRepository,
            instance=True,
        )
        self.cache_provider_mock = create_autospec(CacheProvider, instance=True)
        self.reset_password_context_ttl = Ttl.create(3600)
        self.use_case = VerifyResetPasswordOtpUseCase(
            accounts_repository=self.accounts_repository_mock,
            cache_provider=self.cache_provider_mock,
            reset_password_context_ttl=self.reset_password_context_ttl,
        )

    def test_should_return_reset_context_when_otp_is_valid(self) -> None:
        email = 'maria@example.com'
        account = self._create_account()

        self.cache_provider_mock.get.side_effect = [None, Text.create('123456')]
        self.accounts_repository_mock.find_by_email.return_value = account

        result = self.use_case.execute(email=email, otp='123456')

        self.accounts_repository_mock.find_by_email.assert_called_once_with(
            account.email
        )
        self.cache_provider_mock.set_with_ttl.assert_called_once_with(
            key=CacheKeys().get_reset_password_context(result.reset_context),
            value=Text.create(account.id.value),
            ttl=self.reset_password_context_ttl,
        )
        self.cache_provider_mock.delete.assert_has_calls(
            [
                call(CacheKeys().get_reset_password_otp(email)),
                call(CacheKeys().get_reset_password_otp_attempts(email)),
                call(CacheKeys().get_reset_password_otp_resend_cooldown(email)),
            ]
        )

    def test_should_raise_invalid_reset_password_otp_error_when_otp_is_invalid(
        self,
    ) -> None:
        email = 'maria@example.com'

        self.cache_provider_mock.get.side_effect = [
            Text.create('3'),
            Text.create('654321'),
        ]

        with pytest.raises(InvalidResetPasswordOtpError):
            self.use_case.execute(email=email, otp='123456')

        self.cache_provider_mock.set.assert_called_once_with(
            key=CacheKeys().get_reset_password_otp_attempts(email),
            value=Text.create('2'),
        )
        self.accounts_repository_mock.find_by_email.assert_not_called()
        self.cache_provider_mock.set_with_ttl.assert_not_called()
        self.cache_provider_mock.delete.assert_not_called()

    def test_should_raise_invalid_reset_password_otp_error_when_otp_is_missing_or_expired(
        self,
    ) -> None:
        email = 'maria@example.com'

        self.cache_provider_mock.get.side_effect = [Text.create('3'), None]

        with pytest.raises(InvalidResetPasswordOtpError):
            self.use_case.execute(email=email, otp='123456')

        self.accounts_repository_mock.find_by_email.assert_not_called()
        self.cache_provider_mock.set.assert_not_called()
        self.cache_provider_mock.set_with_ttl.assert_not_called()
        self.cache_provider_mock.delete.assert_not_called()

    def test_should_raise_invalid_reset_password_otp_error_when_attempts_are_exhausted(
        self,
    ) -> None:
        email = 'maria@example.com'

        self.cache_provider_mock.get.return_value = Text.create('0')

        with pytest.raises(InvalidResetPasswordOtpError):
            self.use_case.execute(email=email, otp='123456')

        self.cache_provider_mock.get.assert_called_once_with(
            CacheKeys().get_reset_password_otp_attempts(email)
        )
        self.accounts_repository_mock.find_by_email.assert_not_called()
        self.cache_provider_mock.set.assert_not_called()
        self.cache_provider_mock.set_with_ttl.assert_not_called()
        self.cache_provider_mock.delete.assert_not_called()

    def _create_account(self) -> Account:
        stored_password_hash = Text.create('stored-hash').value

        return Account.create(
            AccountDto(
                id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
                name='Maria Silva',
                email='maria@example.com',
                password=stored_password_hash,
                is_verified=True,
                is_active=True,
                social_accounts=[],
            )
        )
