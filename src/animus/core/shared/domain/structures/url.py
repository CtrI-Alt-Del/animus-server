from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.errors import ValidationError


@structure
class Url(Structure):
    value: str

    @classmethod
    def create(cls, value: str) -> 'Url':
        if not value.startswith('http'):
            raise ValidationError(f'Url deve começar com http, recebido: {value}')
        return cls(value=value)
