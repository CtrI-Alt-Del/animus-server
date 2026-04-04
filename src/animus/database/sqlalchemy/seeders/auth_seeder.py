from animus.core.auth.interfaces.accounts_repository import AccountsRepository
from animus.core.auth.interfaces.hash_provider import HashProvider
from animus.core.shared.domain.structures import Id, Text
from animus.fakers.auth.entities.accounts_faker import AccountsFaker


class AuthSeeder:
    def __init__(
        self, accounts_repository: AccountsRepository, hash_provider: HashProvider
    ) -> None:
        self._accounts_repository = accounts_repository
        self._hash_provider = hash_provider

    def seed(self) -> list[Id]:
        account_email = "animus.ctrlaltdel@gmail.com"
        account_password = "Senha@123"

        account = AccountsFaker.fake(
            name="Juan Hassam",
            email=account_email,
            password=account_password,
            is_verified=True,
        )
        password_hash = None
        if account.password is not None:
            password_hash = self._hash_provider.generate(
                Text.create(account.password.value)
            )

        self._accounts_repository.add(account, password_hash)

        return [account.id]
