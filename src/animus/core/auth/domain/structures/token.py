from datetime import datetime

from animus.core.auth.domain.structures.dtos.token_dto import TokenDto
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Datetime


@structure
class Token(Structure):
    value: str
    expires_at: Datetime

    @classmethod
    def create(
        cls,
        value: str,
        expires_at: Datetime | datetime | str,
    ) -> 'Token':
        normalized_value = value.strip()

        if not normalized_value:
            raise ValidationError('Token nao pode ser vazio')

        normalized_expires_at = (
            expires_at
            if isinstance(expires_at, Datetime)
            else Datetime.create(expires_at)
        )

        return cls(
            value=normalized_value,
            expires_at=normalized_expires_at,
        )

    def is_expired(self, reference_datetime: Datetime | None = None) -> bool:
        if reference_datetime is None:
            reference_datetime = Datetime.create_at_now()

        return self.expires_at.value <= reference_datetime.value

    @property
    def dto(self) -> TokenDto:
        return TokenDto(
            value=self.value,
            expires_at=self.expires_at.value.isoformat(),
        )
