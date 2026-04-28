from unittest.mock import create_autospec

import pytest

from unittest.mock import call

from animus.constants.cache_keys import CacheKeys
from animus.core.auth.domain.entities import Account
from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.domain.events.password_reset_request_event import (
    PasswordResetRequestEvent,
)
from animus.core.auth.domain.structures import Otp
from animus.core.auth.domain.structures.email import Email
from animus.core.auth.interfaces import AccountsRepository
from animus.core.auth.use_cases.forgot_password_use_case import ForgotPasswordUseCase
from animus.core.shared.domain.structures import Text, Ttl
from animus.core.shared.interfaces import CacheProvider, OtpProvider
from animus.core.shared.interfaces.broker import Broker


class TestForgotPasswordUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.accounts_repository_mock = create_autospec(
            AccountsRepository,
            instance=True,
        )
        self.otp_provider_mock = create_autospec(OtpProvider, instance=True)
        self.cache_provider_mock = create_autospec(CacheProvider, instance=True)
        self.broker_mock = create_autospec(Broker, instance=True)
        self.reset_password_otp_ttl = Ttl.create(3600)
        self.reset_password_otp_resend_cooldown_ttl = Ttl.create(60)
        self.use_case = ForgotPasswordUseCase(
            accounts_repository=self.accounts_repository_mock,
            otp_provider=self.otp_provider_mock,
            cache_provider=self.cache_provider_mock,
            broker=self.broker_mock,
            reset_password_otp_ttl=self.reset_password_otp_ttl,
            reset_password_otp_resend_cooldown_ttl=(
                self.reset_password_otp_resend_cooldown_ttl
            ),
        )

    def test_should_generate_otp_cache_it_and_publish_event_when_account_exists(
        self,
    ) -> None:
        email_str = 'maria@example.com'
        account = self._create_account()

        self.accounts_repository_mock.find_by_email.return_value = account
        self.cache_provider_mock.get.return_value = None
        self.otp_provider_mock.generate.return_value = Otp.create('123456')

        self.use_case.execute(email=email_str)

        expected_email_vo = Email.create(email_str)
        self.accounts_repository_mock.find_by_email.assert_called_once_with(
            expected_email_vo
        )
        self.cache_provider_mock.get.assert_called_once_with(
            CacheKeys().get_reset_password_otp_resend_cooldown(email_str)
        )
        self.otp_provider_mock.generate.assert_called_once_with()
        self.cache_provider_mock.set_with_ttl.assert_has_calls(
            [
                call(
                    key=CacheKeys().get_reset_password_otp(email_str),
                    value=Text.create('123456'),
                    ttl=self.reset_password_otp_ttl,
                ),
                call(
                    key=CacheKeys().get_reset_password_otp_resend_cooldown(email_str),
                    value=Text.create('123456'),
                    ttl=self.reset_password_otp_resend_cooldown_ttl,
                ),
            ]
        )
        self.cache_provider_mock.set.assert_called_once_with(
            key=CacheKeys().get_reset_password_otp_attempts(email_str),
            value=Text.create(str(Otp.MAX_VERIFICATION_ATTEMPTS)),
        )

        expected_event = PasswordResetRequestEvent(
            account_email=account.email.value,
            account_email_otp='123456',
        )
        self.broker_mock.publish.assert_called_once_with(expected_event)

    def test_should_return_silently_when_account_does_not_exist(self) -> None:
        email_str = 'ghost@example.com'

        self.accounts_repository_mock.find_by_email.return_value = None

        self.use_case.execute(email=email_str)

        expected_email_vo = Email.create(email_str)
        self.accounts_repository_mock.find_by_email.assert_called_once_with(
            expected_email_vo
        )

        self.otp_provider_mock.generate.assert_not_called()
        self.cache_provider_mock.get.assert_not_called()
        self.cache_provider_mock.set.assert_not_called()
        self.cache_provider_mock.set_with_ttl.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_return_silently_when_reset_password_cooldown_is_active(
        self,
    ) -> None:
        email_str = 'maria@example.com'
        account = self._create_account()

        self.accounts_repository_mock.find_by_email.return_value = account
        self.cache_provider_mock.get.return_value = Text.create('123456')

        self.use_case.execute(email=email_str)

        self.cache_provider_mock.get.assert_called_once_with(
            CacheKeys().get_reset_password_otp_resend_cooldown(email_str)
        )
        self.otp_provider_mock.generate.assert_not_called()
        self.cache_provider_mock.set.assert_not_called()
        self.cache_provider_mock.set_with_ttl.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def _create_account(self) -> Account:
        return Account.create(
            AccountDto(
                id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
                name='Maria Silva',
                email='maria@example.com',
                password=None,
                is_verified=True,
                is_active=True,
                social_accounts=[],
            )
        )
