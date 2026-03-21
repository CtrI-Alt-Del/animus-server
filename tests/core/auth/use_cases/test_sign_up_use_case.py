from unittest.mock import create_autospec

import pytest

from animus.core.auth.domain.errors import (
    AccountAlreadyExistsError,
    AccountNotFoundError,
)
from animus.core.auth.domain.events import EmailVerificationRequestedEvent
from animus.core.auth.interfaces import (
    AccountsRepository,
    EmailVerificationProvider,
    HashProvider,
)
from animus.core.auth.use_cases import SignUpUseCase
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Text
from animus.core.shared.interfaces import Broker


class TestSignUpUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.accounts_repository_mock = create_autospec(
            AccountsRepository,
            instance=True,
        )
        self.hash_provider_mock = create_autospec(HashProvider, instance=True)
        self.email_verification_provider_mock = create_autospec(
            EmailVerificationProvider,
            instance=True,
        )
        self.broker_mock = create_autospec(Broker, instance=True)
        self.use_case = SignUpUseCase(
            accounts_repository=self.accounts_repository_mock,
            hash_provider=self.hash_provider_mock,
            email_verification_provider=self.email_verification_provider_mock,
            broker=self.broker_mock,
        )

    def test_should_create_account_and_publish_verification_event(self) -> None:
        valid_password = 'Password123'  # noqa: S105

        self.accounts_repository_mock.find_by_email.side_effect = AccountNotFoundError()
        self.hash_provider_mock.generate.return_value = Text.create('hashed-password')
        self.email_verification_provider_mock.generate_verification_token.return_value = Text.create(
            'verification-token'
        )

        result = self.use_case.execute(
            name='Maria Silva',
            email='maria@example.com',
            password=valid_password,
        )

        self.hash_provider_mock.generate.assert_called_once_with(
            Text.create(valid_password)
        )
        self.accounts_repository_mock.add.assert_called_once()
        self.broker_mock.publish.assert_called_once()
        created_account, saved_password_hash = (
            self.accounts_repository_mock.add.call_args.args
        )
        published_event = self.broker_mock.publish.call_args.args[0]
        assert created_account.name.value == 'Maria Silva'
        assert created_account.email.value == 'maria@example.com'
        assert created_account.password.value == 'Password123'
        assert saved_password_hash.value == 'hashed-password'
        assert isinstance(published_event, EmailVerificationRequestedEvent)
        assert published_event.payload_data == {
            'account_email': 'maria@example.com',
            'account_email_verification_token': 'verification-token',
        }
        assert result.name == 'Maria Silva'
        assert result.email == 'maria@example.com'
        assert result.password is None
        assert result.is_verified is False
        assert result.is_active is True

    def test_should_raise_account_already_exists_error_when_email_already_exists(
        self,
    ) -> None:
        valid_password = 'Password123'  # noqa: S105

        self.accounts_repository_mock.find_by_email.return_value = object()

        with pytest.raises(AccountAlreadyExistsError):
            self.use_case.execute(
                name='Maria Silva',
                email='maria@example.com',
                password=valid_password,
            )

        self.hash_provider_mock.generate.assert_not_called()
        self.accounts_repository_mock.add.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_validation_error_when_password_is_weak(self) -> None:
        weak_password = 'weak'  # noqa: S105

        with pytest.raises(ValidationError, match='pelo menos 8 caracteres'):
            self.use_case.execute(
                name='Maria Silva',
                email='maria@example.com',
                password=weak_password,
            )

        self.accounts_repository_mock.find_by_email.assert_not_called()
        self.hash_provider_mock.generate.assert_not_called()
        self.accounts_repository_mock.add.assert_not_called()
        self.broker_mock.publish.assert_not_called()
