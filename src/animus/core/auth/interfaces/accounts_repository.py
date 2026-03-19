from typing import Protocol

from animus.core.auth.domain.entities import Account
from animus.core.auth.domain.structures.email import Email
from animus.core.shared.domain.structures import Id


class AccountsRepository(Protocol):
    def find_by_id(self, account_id: Id) -> Account: ...

    def find_by_email(self, email: Email) -> Account: ...

    def add(self, account: Account) -> None: ...

    def add_many(self, accounts: list[Account]) -> None: ...

    def replace(self, account: Account) -> None: ...
