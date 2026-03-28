from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.errors import ValidationError


@structure
class Decimal(Structure):
    value: float

    @classmethod
    def create(cls, value: float) -> 'Decimal':
        if not isinstance(value, float):
            raise ValidationError(
                f'Valor deve ser um valor com ponto flutuante, recebido: {value}'
            )

        return cls(value=value)
