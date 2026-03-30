from faker import Faker

from animus.core.auth.domain.entities.account import Account
from animus.core.auth.domain.entities.dtos.account_dto import AccountDto
from animus.core.shared.domain.structures import Id


class AccountsFaker:
    _faker = Faker()

    @staticmethod
    def fake(
        account_id: str | None = None,
        name: str | None = None,
        email: str | None = None,
        password: str | None = None,
        is_verified: bool = True,
        is_active: bool = True,
    ) -> Account:
        return Account.create(
            AccountsFaker.fake_dto(
                account_id=account_id,
                name=name,
                email=email,
                password=password,
                is_verified=is_verified,
                is_active=is_active,
            )
        )

    @staticmethod
    def fake_dto(
        account_id: str | None = None,
        name: str | None = None,
        email: str | None = None,
        password: str | None = None,
        is_verified: bool = True,
        is_active: bool = True,
    ) -> AccountDto:
        return AccountDto(
            id=account_id or Id.create().value,
            name=name or AccountsFaker._faker.name(),
            email=email or AccountsFaker._faker.email(),
            password=password or AccountsFaker._faker.password(),
            is_verified=is_verified,
            is_active=is_active,
        )

    @staticmethod
    def fake_many(count: int) -> list[Account]:
        return [AccountsFaker.fake() for _ in range(count)]

    @staticmethod
    def fake_many_dto(count: int) -> list[AccountDto]:
        return [AccountsFaker.fake_dto() for _ in range(count)]
