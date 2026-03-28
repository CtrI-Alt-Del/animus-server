from unittest.mock import create_autospec

import pytest

from animus.core.auth.domain.entities import Account
from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.auth.domain.errors import (
    AccountInactiveError,
    AccountNotFoundError,
)
from animus.core.auth.interfaces import AccountsRepository
from animus.core.auth.use_cases import GetAccountUseCase
from animus.core.shared.domain.structures import Id


class TestGetAccountUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.accounts_repository_mock = create_autospec(
            AccountsRepository,
            instance=True,
        )
        self.use_case = GetAccountUseCase(
            accounts_repository=self.accounts_repository_mock,
        )

    def test_should_return_account_dto_when_account_is_found_and_active(self) -> None:
        account_id = Id.create('01ARZ3NDEKTSV4RRFFQ69G5FAV')
        account = Account.create(
            AccountDto(
                id=account_id.value,
                name='Miojo',
                email='miojo@example.com',
                password='hashed',
                is_verified=True,
                is_active=True,
                social_accounts=[],
            )
        )
        self.accounts_repository_mock.find_by_id.return_value = account

        result = self.use_case.execute(account_id=account_id)

        self.accounts_repository_mock.find_by_id.assert_called_once_with(account_id)
        assert result.id == account_id.value
        assert result.name == 'Miojo'
        assert result.email == 'miojo@example.com'
        assert result.is_verified is True
        assert result.is_active is True

    def test_should_raise_not_found_error_when_account_does_not_exist(self) -> None:
        account_id = Id.create('01ARZ3NDEKTSV4RRFFQ69G5FAV')
        self.accounts_repository_mock.find_by_id.side_effect = AccountNotFoundError()

        with pytest.raises(AccountNotFoundError):
            self.use_case.execute(account_id=account_id)

        self.accounts_repository_mock.find_by_id.assert_called_once_with(account_id)

    def test_should_raise_inactive_error_when_account_is_inactive(self) -> None:
        account_id = Id.create('01ARZ3NDEKTSV4RRFFQ69G5FAV')
        account = Account.create(
            AccountDto(
                id=account_id.value,
                name='Miojo',
                email='miojo@example.com',
                password='hashed',
                is_verified=True,
                is_active=False,
                social_accounts=[],
            )
        )
        self.accounts_repository_mock.find_by_id.return_value = account

        with pytest.raises(AccountInactiveError):
            self.use_case.execute(account_id=account_id)

        self.accounts_repository_mock.find_by_id.assert_called_once_with(account_id)
