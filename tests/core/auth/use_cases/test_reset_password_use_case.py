from unittest.mock import create_autospec

import pytest

from animus.core.auth.domain.entities import Account
from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.domain.errors.account_not_found_error import AccountNotFoundError
from animus.core.auth.interfaces.accounts_repository import AccountsRepository
from animus.core.auth.interfaces.hash_provider import HashProvider
from animus.core.auth.use_cases.reset_password_use_case import ResetPasswordUseCase
from animus.core.shared.domain.structures.id import Id
from animus.core.shared.domain.structures.text import Text



class TestResetPasswordUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.accounts_repository_mock = create_autospec(
            AccountsRepository,
            instance=True,
        )
        self.hash_provider_mock = create_autospec(HashProvider, instance=True)
        self.use_case = ResetPasswordUseCase(
            accounts_repository=self.accounts_repository_mock,
            hash_provider=self.hash_provider_mock,
        )

    def test_should_update_password_when_account_exists(self) -> None:
        account_id_str = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        new_password_str = 'NewStrongPassword123'
        account = self._create_account()
        hashed_password = Text.create('new-hashed-password')

        self.accounts_repository_mock.find_by_id.return_value = account
        self.hash_provider_mock.generate.return_value = hashed_password

        self.use_case.execute(
            account_id=account_id_str,
            new_password=new_password_str,
        )

        expected_id_vo = Id.create(account_id_str)
        self.accounts_repository_mock.find_by_id.assert_called_once_with(
            expected_id_vo
        )

        expected_password_vo = Text.create(new_password_str)
        self.hash_provider_mock.generate.assert_called_once_with(
            expected_password_vo
        )

        assert account.password == hashed_password
        self.accounts_repository_mock.replace.assert_called_once_with(account)

    def test_should_raise_account_not_found_error_when_account_does_not_exist(
        self,
    ) -> None:
        account_id_str = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        new_password_str = 'NewStrongPassword123'

        self.accounts_repository_mock.find_by_id.return_value = None

        with pytest.raises(AccountNotFoundError):
            self.use_case.execute(
                account_id=account_id_str,
                new_password=new_password_str,
            )

        expected_id_vo = Id.create(account_id_str)
        self.accounts_repository_mock.find_by_id.assert_called_once_with(
            expected_id_vo
        )

        self.hash_provider_mock.generate.assert_not_called()
        self.accounts_repository_mock.replace.assert_not_called()

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
