from animus.core.auth.domain.entities.dtos.account_dto import AccountDto
from animus.core.auth.domain.entities.social_account import SocialAccount
from animus.core.auth.domain.structures.email import Email
from animus.core.shared.domain.abstracts import Entity
from animus.core.shared.domain.decorators import entity
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id, Logical, Name, Text


@entity
class Account(Entity):
    id: Id
    name: Name
    email: Email
    password: Text | None
    is_verified: Logical
    is_active: Logical
    social_accounts: list[SocialAccount]

    @classmethod
    def create(cls, dto: AccountDto) -> 'Account':
        password = Text.create(dto.password) if dto.password else None
        return cls(
            id=Id.create(dto.id),
            name=Name.create(dto.name),
            email=Email.create(dto.email),
            password=password,
            is_verified=Logical.create(dto.is_verified),
            is_active=Logical.create(dto.is_active),
            social_accounts=[
                SocialAccount.create(social_account)
                for social_account in dto.social_accounts or []
            ],
        )

    @property
    def dto(self) -> AccountDto:
        return AccountDto(
            id=self.id.value,
            name=self.name.value,
            email=self.email.value,
            password=self.password.value if self.password is not None else None,
            is_verified=self.is_verified.value,
            is_active=self.is_active.value,
            social_accounts=[item.dto for item in self.social_accounts],
        )

    def verify(self) -> None:
        self.is_verified = Logical.create_true()

    def activate(self) -> None:
        self.is_active = Logical.create_true()

    def deactivate(self) -> None:
        self.is_active = Logical.create_false()

    def add_social_account(self, social_account: SocialAccount) -> None:
        has_social_account = any(
            item.email == social_account.email
            and item.provider == social_account.provider
            for item in self.social_accounts
        )

        if has_social_account:
            raise ValidationError('Conta social ja vinculada para esse provedor')

        self.social_accounts.append(social_account)
