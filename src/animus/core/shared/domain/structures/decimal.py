from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.errors import ValidationError


@structure
class Decimal(Structure):
    value: float

    @classmethod
    def create(cls, value: float) -> 'Decimal':
        if value < 0.0:
            raise ValidationError(
                f'Valor deve ser maior ou igual a 0.0, recebido: {value}'
            )

        return cls(value=value)
