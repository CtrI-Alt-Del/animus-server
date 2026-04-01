from unittest.mock import create_autospec

import pytest

from animus.core.auth.domain.entities import Account
from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.domain.events.password_reset_request_event import (
    PasswordResetRequestEvent,
)
from animus.core.auth.domain.structures.email import Email
from animus.core.auth.interfaces import AccountsRepository
from animus.core.auth.use_cases.forgot_password_use_case import ForgotPasswordUseCase
from animus.core.shared.interfaces.broker import Broker


class TestForgotPasswordUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.accounts_repository_mock = create_autospec(
            AccountsRepository,
            instance=True,
        )
        self.broker_mock = create_autospec(Broker, instance=True)
        self.use_case = ForgotPasswordUseCase(
            accounts_repository=self.accounts_repository_mock,
            broker=self.broker_mock,
        )

    def test_should_publish_event_when_account_exists(self) -> None:
        email_str = 'maria@example.com'
        account = self._create_account()

        self.accounts_repository_mock.find_by_email.return_value = account

        self.use_case.execute(email=email_str)

        expected_email_vo = Email.create(email_str)
        self.accounts_repository_mock.find_by_email.assert_called_once_with(
            expected_email_vo
        )

        expected_event = PasswordResetRequestEvent(account_email=account.email)
        self.broker_mock.publish.assert_called_once_with(expected_event)

    def test_should_return_silently_when_account_does_not_exist(self) -> None:
        email_str = 'ghost@example.com'

        self.accounts_repository_mock.find_by_email.return_value = None

        self.use_case.execute(email=email_str)

        expected_email_vo = Email.create(email_str)
        self.accounts_repository_mock.find_by_email.assert_called_once_with(
            expected_email_vo
        )
        
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
