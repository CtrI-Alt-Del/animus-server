import re

from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


@structure
class Otp(Structure):
    value: str
    MAX_VERIFICATION_ATTEMPTS: int = 3

    @classmethod
    def create(cls, value: str) -> 'Otp':
        normalized = value.strip()

        if not re.fullmatch(r'\d{6}', normalized):
            raise ValidationError(
                f'OTP inválido: deve conter exatamente 6 digitos numericos, recebido: {value!r}'
            )

        return cls(value=normalized)

    @property
    def dto(self) -> str:
        return self.value
