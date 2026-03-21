from unittest.mock import create_autospec

import pytest

from animus.core.auth.domain.entities import Account
from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.domain.errors import AccountAlreadyVerifiedError
from animus.core.auth.domain.events import EmailVerificationRequestedEvent
from animus.core.auth.interfaces import AccountsRepository, EmailVerificationProvider
from animus.core.auth.use_cases import ResendVerificationEmailUseCase
from animus.core.shared.domain.structures import Text
from animus.core.shared.interfaces import Broker


class TestResendVerificationEmailUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.accounts_repository_mock = create_autospec(
            AccountsRepository,
            instance=True,
        )
        self.email_verification_provider_mock = create_autospec(
            EmailVerificationProvider,
            instance=True,
        )
        self.broker_mock = create_autospec(Broker, instance=True)
        self.use_case = ResendVerificationEmailUseCase(
            accounts_repository=self.accounts_repository_mock,
            email_verification_provider=self.email_verification_provider_mock,
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
        self.email_verification_provider_mock.generate_verification_token.return_value = Text.create(
            'verification-token'
        )

        self.use_case.execute(email='maria@example.com')

        self.email_verification_provider_mock.generate_verification_token.assert_called_once()
        self.broker_mock.publish.assert_called_once()
        published_event = self.broker_mock.publish.call_args.args[0]
        assert isinstance(published_event, EmailVerificationRequestedEvent)
        assert published_event.payload_data == {
            'account_email': 'maria@example.com',
            'account_email_verification_token': 'verification-token',
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

        self.email_verification_provider_mock.generate_verification_token.assert_not_called()
        self.broker_mock.publish.assert_not_called()
