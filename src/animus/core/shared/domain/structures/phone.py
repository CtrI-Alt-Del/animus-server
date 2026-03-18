from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


@structure
class Phone(Structure):
    value: str

    @staticmethod
    def create(value: str) -> 'Phone':
        if not value.isdigit() or len(value) != 11:
            raise ValidationError(
                f'Telefone deve conter exatamente 11 digitos, recebido: {value}'
            )

        return Phone(value=value)
