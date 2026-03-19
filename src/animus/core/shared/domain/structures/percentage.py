from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


@structure
class Percentage(Structure):
    value: float

    @classmethod
    def create(cls, value: float) -> 'Percentage':
        if value < 0.0 or value > 100.0:
            raise ValidationError(
                f'Valor deve estar entre 0.0 e 100.0, recebido: {value}'
            )

        return cls(value=value)
