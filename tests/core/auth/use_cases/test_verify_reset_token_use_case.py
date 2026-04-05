from unittest.mock import create_autospec

import pytest

from animus.core.auth.domain.entities import Account
from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.domain.errors.invalid_email_verification_token_error import (
    InvalidEmailVerificationTokenError,
)
from animus.core.auth.domain.structures.email import Email
from animus.core.auth.interfaces.accounts_repository import AccountsRepository
from animus.core.auth.interfaces.email_verification_provider import (
    EmailVerificationProvider,
)
from animus.core.auth.use_cases.verify_reset_token_use_case import (
    VerifyResetTokenUseCase,
)
from animus.core.shared.domain.structures import Logical
from animus.core.shared.domain.structures.text import Text


class TestVerifyResetTokenUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.email_verification_provider_mock = create_autospec(
            EmailVerificationProvider,
            instance=True,
        )
        self.accounts_repository_mock = create_autospec(
            AccountsRepository,
            instance=True,
        )
        self.use_case = VerifyResetTokenUseCase(
            email_verification_provider=self.email_verification_provider_mock,
            accounts_repository=self.accounts_repository_mock,
        )

    def test_should_return_account_id_when_token_is_valid_and_account_exists(
        self,
    ) -> None:
        token_str = 'valid-jwt-token'
        account = self._create_account()
        decoded_email = Email.create('maria@example.com')

        self.email_verification_provider_mock.verify_verification_token.return_value = (
            Logical.create_true()
        )
        self.email_verification_provider_mock.decode_email_from_token.return_value = (
            decoded_email
        )
        self.accounts_repository_mock.find_by_email.return_value = account

        result = self.use_case.execute(token=token_str)

        expected_token_vo = Text.create(token_str)

        self.email_verification_provider_mock.verify_verification_token.assert_called_once_with(
            expected_token_vo
        )
        self.email_verification_provider_mock.decode_email_from_token.assert_called_once_with(
            expected_token_vo
        )
        self.accounts_repository_mock.find_by_email.assert_called_once_with(
            decoded_email
        )
        assert result == account.id.value

    def test_should_raise_error_when_token_is_invalid(self) -> None:
        token_str = 'invalid-jwt-token'

        self.email_verification_provider_mock.verify_verification_token.return_value = (
            Logical.create_false()
        )

        with pytest.raises(InvalidEmailVerificationTokenError):
            self.use_case.execute(token=token_str)

        expected_token_vo = Text.create(token_str)
        self.email_verification_provider_mock.verify_verification_token.assert_called_once_with(
            expected_token_vo
        )
        self.email_verification_provider_mock.decode_email_from_token.assert_not_called()
        self.accounts_repository_mock.find_by_email.assert_not_called()

    def test_should_raise_error_when_token_is_valid_but_account_does_not_exist(
        self,
    ) -> None:
        token_str = 'valid-jwt-token-for-deleted-account'
        decoded_email = Email.create('ghost@example.com')

        self.email_verification_provider_mock.verify_verification_token.return_value = (
            Logical.create_true()
        )
        self.email_verification_provider_mock.decode_email_from_token.return_value = (
            decoded_email
        )
        self.accounts_repository_mock.find_by_email.return_value = None

        with pytest.raises(InvalidEmailVerificationTokenError):
            self.use_case.execute(token=token_str)

        expected_token_vo = Text.create(token_str)
        self.email_verification_provider_mock.verify_verification_token.assert_called_once_with(
            expected_token_vo
        )
        self.email_verification_provider_mock.decode_email_from_token.assert_called_once_with(
            expected_token_vo
        )
        self.accounts_repository_mock.find_by_email.assert_called_once_with(
            decoded_email
        )

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
