from unittest.mock import create_autospec

import pytest

from animus.constants.cache_keys import CacheKeys
from animus.core.auth.domain.entities import Account
from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.domain.errors import AccountAlreadyVerifiedError
from animus.core.auth.domain.events import EmailVerificationRequestedEvent
from animus.core.auth.domain.structures import Otp
from animus.core.auth.interfaces import AccountsRepository
from animus.core.auth.use_cases import ResendVerificationEmailUseCase
from animus.core.shared.interfaces import Broker, CacheProvider, OtpProvider


class TestResendVerificationEmailUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.accounts_repository_mock = create_autospec(
            AccountsRepository,
            instance=True,
        )
        self.otp_provider_mock = create_autospec(
            OtpProvider,
            instance=True,
        )
        self.cache_provider_mock = create_autospec(
            CacheProvider,
            instance=True,
        )
        self.broker_mock = create_autospec(Broker, instance=True)
        self.use_case = ResendVerificationEmailUseCase(
            accounts_repository=self.accounts_repository_mock,
            otp_provider=self.otp_provider_mock,
            cache_provider=self.cache_provider_mock,
            broker=self.broker_mock,
        )

    def test_should_publish_verification_event_when_account_is_not_verified(
        self,
    ) -> None:
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
        self.accounts_repository_mock.find_by_email.return_value = account
        self.otp_provider_mock.generate.return_value = Otp.create('123456')

        self.use_case.execute(email='maria@example.com')

        self.otp_provider_mock.generate.assert_called_once_with()
        self.cache_provider_mock.set_with_ttl.assert_called_once()
        self.broker_mock.publish.assert_called_once()
        published_event = self.broker_mock.publish.call_args.args[0]
        assert isinstance(published_event, EmailVerificationRequestedEvent)
        cache_call = self.cache_provider_mock.set_with_ttl.call_args.kwargs
        assert cache_call['key'] == CacheKeys().get_email_verification(
            'maria@example.com'
        )
        assert cache_call['value'].value == '123456'
        assert cache_call['ttl'].seconds == 3600
        assert published_event.payload_data == {
            'account_email': 'maria@example.com',
            'account_email_otp': '123456',
        }

    def test_should_raise_account_already_verified_error_when_account_is_verified(
        self,
    ) -> None:
        account = Account.create(
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
        self.accounts_repository_mock.find_by_email.return_value = account

        with pytest.raises(AccountAlreadyVerifiedError):
            self.use_case.execute(email='maria@example.com')

        self.otp_provider_mock.generate.assert_not_called()
        self.cache_provider_mock.set_with_ttl.assert_not_called()
        self.broker_mock.publish.assert_not_called()
