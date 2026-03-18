import re

from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.errors import ValidationError


@structure
class Email(Structure):
    value: str

    @staticmethod
    def create(value: str) -> 'Email':
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise ValidationError(f'Email invalido: {value}')

        return Email(value=value)
