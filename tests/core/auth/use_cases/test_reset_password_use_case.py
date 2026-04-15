from unittest.mock import create_autospec

import pytest

from animus.constants.cache_keys import CacheKeys
from animus.core.auth.domain.entities import Account
from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.domain.errors import InvalidResetPasswordContextError
from animus.core.auth.interfaces.accounts_repository import AccountsRepository
from animus.core.auth.interfaces.hash_provider import HashProvider
from animus.core.auth.use_cases.reset_password_use_case import ResetPasswordUseCase
from animus.core.shared.interfaces import CacheProvider
from animus.core.shared.domain.structures.text import Text


class TestResetPasswordUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.accounts_repository_mock = create_autospec(
            AccountsRepository,
            instance=True,
        )
        self.cache_provider_mock = create_autospec(CacheProvider, instance=True)
        self.hash_provider_mock = create_autospec(HashProvider, instance=True)
        self.use_case = ResetPasswordUseCase(
            accounts_repository=self.accounts_repository_mock,
            cache_provider=self.cache_provider_mock,
            hash_provider=self.hash_provider_mock,
        )

    def test_should_update_password_when_reset_context_is_valid(self) -> None:
        reset_context = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        new_password_str = 'NewStrongPassword123'
        account = self._create_account()
        hashed_password = Text.create('new-hashed-password')

        self.cache_provider_mock.get.return_value = Text.create(account.id.value)
        self.accounts_repository_mock.find_by_id.return_value = account
        self.hash_provider_mock.generate.return_value = hashed_password

        self.use_case.execute(
            reset_context=reset_context,
            new_password=new_password_str,
        )

        self.cache_provider_mock.get.assert_called_once_with(
            CacheKeys().get_reset_password_context(reset_context)
        )
        self.accounts_repository_mock.find_by_id.assert_called_once_with(account.id)
        expected_password_vo = Text.create(new_password_str)
        self.hash_provider_mock.generate.assert_called_once_with(expected_password_vo)

        assert account.password == hashed_password
        self.accounts_repository_mock.replace.assert_called_once_with(account)
        self.cache_provider_mock.delete.assert_called_once_with(
            CacheKeys().get_reset_password_context(reset_context)
        )

    def test_should_raise_invalid_reset_password_context_error_when_context_is_missing(
        self,
    ) -> None:
        reset_context = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        new_password_str = 'NewStrongPassword123'

        self.cache_provider_mock.get.return_value = None

        with pytest.raises(InvalidResetPasswordContextError):
            self.use_case.execute(
                reset_context=reset_context,
                new_password=new_password_str,
            )

        self.cache_provider_mock.get.assert_called_once_with(
            CacheKeys().get_reset_password_context(reset_context)
        )
        self.accounts_repository_mock.find_by_id.assert_not_called()
        self.hash_provider_mock.generate.assert_not_called()
        self.accounts_repository_mock.replace.assert_not_called()
        self.cache_provider_mock.delete.assert_not_called()

    def test_should_raise_invalid_reset_password_context_error_when_account_does_not_exist(
        self,
    ) -> None:
        reset_context = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        new_password_str = 'NewStrongPassword123'

        self.cache_provider_mock.get.return_value = Text.create(
            '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        )
        self.accounts_repository_mock.find_by_id.return_value = None

        with pytest.raises(InvalidResetPasswordContextError):
            self.use_case.execute(
                reset_context=reset_context,
                new_password=new_password_str,
            )

        self.accounts_repository_mock.find_by_id.assert_called_once()
        self.hash_provider_mock.generate.assert_not_called()
        self.accounts_repository_mock.replace.assert_not_called()
        self.cache_provider_mock.delete.assert_not_called()

    def _create_account(self) -> Account:
        return Account.create(
            AccountDto(
                id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
                name='Maria Silva',
                email='maria@example.com',
                password=Text.create('old-hashed-password').value,
                is_verified=True,
                is_active=True,
                social_accounts=[],
            )
        )
