from sqlalchemy import select
from sqlalchemy.orm import Session

from animus.core.auth.domain.entities import Account
from animus.core.auth.domain.errors import AccountNotFoundError
from animus.core.auth.domain.structures.email import Email
from animus.core.auth.interfaces import AccountsRepository
from animus.core.shared.domain.structures import Id, Text
from animus.database.sqlalchemy.mappers.auth import AccountMapper
from animus.database.sqlalchemy.models.auth import AccountModel


class SqlalchemyAccountsRepository(AccountsRepository):
    def __init__(self, sqlalchemy: Session) -> None:
        self._sqlalchemy = sqlalchemy

    def find_by_id(self, account_id: Id) -> Account:
        model = self._sqlalchemy.get(AccountModel, account_id.value)
        if model is None:
            raise AccountNotFoundError

        return AccountMapper.to_entity(model)

    def find_by_email(self, email: Email) -> Account:
        model = self._sqlalchemy.scalar(
            select(AccountModel).where(AccountModel.email == email.value)
        )
        if model is None:
            raise AccountNotFoundError

        return AccountMapper.to_entity(model)

    def add(self, account: Account, password: Text) -> None:
        self._sqlalchemy.add(AccountMapper.to_model(account, password))

    def add_many(self, accounts: list[tuple[Account, Text]]) -> None:
        self._sqlalchemy.add_all(
            [
                AccountMapper.to_model(account=account, password_hash=password_hash)
                for account, password_hash in accounts
            ]
        )

    def replace(self, account: Account) -> None:
        model = self._sqlalchemy.get(AccountModel, account.id.value)
        if model is None:
            raise AccountNotFoundError

        model.name = account.name.value
        model.is_verified = account.is_verified.value
        model.is_active = account.is_active.value
