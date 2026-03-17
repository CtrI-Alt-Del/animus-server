from pydantic import ValidationError
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.abstracts import Structure


@structure
class Phone(Structure):
    value: str

    @staticmethod
    def create(value: str) -> 'Phone':
        if not value.isdigit() or len(value) != 11:
            raise ValidationError(f'Telefone deve ter 11 dígitos, got {value}')
        return Phone(value=value)
