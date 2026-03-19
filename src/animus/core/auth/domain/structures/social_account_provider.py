from enum import StrEnum

from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


class SocialAccountProviderValue(StrEnum):
    GOOGLE = 'GOOGLE'


@structure
class SocialAccountProvider(Structure):
    value: SocialAccountProviderValue

    @classmethod
    def create(
        cls,
        value: SocialAccountProviderValue | str,
    ) -> 'SocialAccountProvider':
        if isinstance(value, SocialAccountProviderValue):
            return cls(value=value)

        try:
            provider_value = SocialAccountProviderValue(value.upper())
        except ValueError as error:
            raise ValidationError(f'Provedor social invalido: {value}') from error

        return cls(value=provider_value)

    @property
    def dto(self) -> str:
        return self.value.value
