from animus.core.auth.domain.entities import Account
from animus.core.auth.domain.entities.dtos import AccountDto
from animus.core.shared.domain.structures import Text
from animus.database.sqlalchemy.models.auth import AccountModel


class AccountMapper:
    @staticmethod
    def to_entity(model: AccountModel) -> Account:
        return Account.create(
            AccountDto(
                id=model.id,
                name=model.name,
                email=model.email,
                password=None,
                is_verified=model.is_verified,
                is_active=model.is_active,
                social_accounts=[],
            )
        )

    @staticmethod
    def to_model(account: Account, password_hash: Text | None) -> AccountModel:
        return AccountModel(
            id=account.id.value,
            name=account.name.value,
            email=account.email.value,
            password_hash=password_hash.value if password_hash else None,
            is_verified=account.is_verified.value,
            is_active=account.is_active.value,
        )
