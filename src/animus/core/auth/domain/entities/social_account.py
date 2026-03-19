from animus.core.auth.domain.entities.dtos.social_account_dto import SocialAccountDto
from animus.core.auth.domain.structures import SocialAccountProvider
from animus.core.auth.domain.structures.email import Email
from animus.core.shared.domain.abstracts import Entity
from animus.core.shared.domain.decorators import entity
from animus.core.shared.domain.structures import Id, Name


@entity
class SocialAccount(Entity):
    id: Id
    name: Name
    email: Email
    provider: SocialAccountProvider

    @classmethod
    def create(cls, dto: SocialAccountDto) -> 'SocialAccount':
        return cls(
            id=Id.create(dto.id),
            name=Name.create(dto.name),
            email=Email.create(dto.email),
            provider=SocialAccountProvider.create(dto.provider),
        )

    @property
    def dto(self) -> SocialAccountDto:
        return SocialAccountDto(
            id=self.id.value,
            name=self.name.value,
            email=self.email.value,
            provider=self.provider.value.value,
        )
