from unittest.mock import create_autospec

import pytest

from animus.core.auth.domain.entities import Account
from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.domain.errors import AccountNotFoundError
from animus.core.auth.interfaces import AccountsRepository
from animus.core.auth.use_cases import UpdateAccountUseCase
from animus.core.shared.domain.errors import ValidationError


class TestUpdateAccountUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.accounts_repository_mock = create_autospec(
            AccountsRepository, instance=True
        )
        self.use_case = UpdateAccountUseCase(
            accounts_repository=self.accounts_repository_mock
        )

    def test_should_update_account_name_when_account_exists_and_name_is_valid(
        self,
    ) -> None:
        account_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        new_name = 'Novo Nome'
        account = self._create_account(id=account_id, name='Nome Antigo')

        self.accounts_repository_mock.find_by_id.return_value = account

        self.use_case.execute(account_id=account_id, name=new_name)

        assert account.name.value == new_name
        self.accounts_repository_mock.find_by_id.assert_called_once()
        self.accounts_repository_mock.replace.assert_called_once_with(account)

    def test_should_raise_account_not_found_error_when_account_does_not_exist(
        self,
    ) -> None:
        account_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        self.accounts_repository_mock.find_by_id.return_value = None

        with pytest.raises(AccountNotFoundError):
            self.use_case.execute(account_id=account_id, name='Novo Nome')

        self.accounts_repository_mock.replace.assert_not_called()

    def test_should_raise_validation_error_when_name_is_invalid(self) -> None:
        account_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        invalid_name = 'A'  # Name requires at least 2 characters

        with pytest.raises(ValidationError):
            self.use_case.execute(account_id=account_id, name=invalid_name)

        self.accounts_repository_mock.find_by_id.assert_not_called()
        self.accounts_repository_mock.replace.assert_not_called()

    def _create_account(self, *, id: str, name: str) -> Account:
        return Account.create(
            AccountDto(
                id=id,
                name=name,
                email='maria@example.com',
                password=None,
                is_verified=True,
                is_active=True,
                social_accounts=[],
            )
        )
